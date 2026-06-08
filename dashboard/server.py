"""
dashboard/server.py
────────────────────
Flask SSE server that:
  1. Serves the single-page dashboard (GET /)
  2. Accepts a POST /run  →  starts the pipeline in a background thread
  3. Streams live events via GET /events  (text/event-stream)
  4. Returns current state via GET /state (JSON snapshot for page reload)

Event format (JSON over SSE):
  { "type": "stage_start" | "stage_done" | "log" | "contact" | "send"
            | "complete" | "error" | "confirm_needed" | "confirm_result",
    ...fields }
"""

from __future__ import annotations

import json
import queue
import threading
import time
import traceback
import os
import sys

from flask import Flask, Response, request, jsonify, stream_with_context

# Ensure project root is on path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from dotenv import load_dotenv
load_dotenv()

app = Flask(__name__, static_folder=None)
app.config["SECRET_KEY"] = os.urandom(16)

# ── Shared state ──────────────────────────────────────────────────────────────
_state: dict = {
    "running":    False,
    "done":       False,
    "error":      None,
    "stage":      0,           # 0 = idle, 1-4 = active stage
    "stages":     {1: "idle", 2: "idle", 3: "idle", 4: "idle"},
    "companies":  [],
    "contacts":   [],
    "sent":       0,
    "failed":     0,
    "seed":       "",
    "confirm_needed": False,
    "confirm_contacts": [],
    "logs":       [],          # last 200 log lines
}
_state_lock = threading.Lock()

# One queue per connected SSE client
_client_queues: list[queue.Queue] = []
_queues_lock = threading.Lock()

# Confirmation event — pipeline thread waits, UI sends y/n
_confirm_event = threading.Event()
_confirm_answer: bool = False


# ── Event bus ─────────────────────────────────────────────────────────────────

def _broadcast(event_type: str, **kwargs) -> None:
    """Push a JSON event to every connected SSE client."""
    payload = json.dumps({"type": event_type, **kwargs})
    with _queues_lock:
        for q in list(_client_queues):
            try:
                q.put_nowait(payload)
            except queue.Full:
                pass


def _log(msg: str, level: str = "info") -> None:
    with _state_lock:
        _state["logs"].append({"ts": time.strftime("%H:%M:%S"), "msg": msg, "level": level})
        if len(_state["logs"]) > 200:
            _state["logs"].pop(0)
    _broadcast("log", msg=msg, level=level, ts=time.strftime("%H:%M:%S"))


# ── Patched pipeline IO so it sends events instead of printing ────────────────

class _PipelineIO:
    """
    Monkey-patch target: replaces utils.logger functions with versions
    that also broadcast SSE events while still printing to terminal.
    """
    @staticmethod
    def ok(msg):   _log(_strip_rich(msg), "ok")
    @staticmethod
    def warn(msg): _log(_strip_rich(msg), "warn")
    @staticmethod
    def err(msg):  _log(_strip_rich(msg), "error")
    @staticmethod
    def info(msg): _log(_strip_rich(msg), "info")


def _strip_rich(s: str) -> str:
    import re
    return re.sub(r'\[/?[^\]]*\]', '', str(s))


def _patch_logger():
    import utils.logger as lg
    lg.ok   = _PipelineIO.ok
    lg.warn = _PipelineIO.warn
    lg.err  = _PipelineIO.err
    lg.info = _PipelineIO.info


# ── Pipeline runner (runs in background thread) ───────────────────────────────

def _run_pipeline(seed_domain: str, config: dict) -> None:
    global _confirm_answer

    _patch_logger()

    import utils.checkpoint as ckpt
    import pipeline.stage1_ocean     as s1
    import pipeline.stage2_prospeo   as s2
    import pipeline.stage3_enricher as s3
    import pipeline.stage4_brevo     as s4

    run_id = ckpt.new_run_id(seed_domain)
    ckpt.save_meta(run_id, seed_domain)

    with _state_lock:
        _state["running"] = True
        _state["done"]    = False
        _state["error"]   = None
        _state["seed"]    = seed_domain
        _state["stages"]  = {1:"active", 2:"idle", 3:"idle", 4:"idle"}

    _broadcast("pipeline_start", seed=seed_domain, run_id=run_id)

    try:
        # ── Stage 1 ──────────────────────────────────────────────────────────
        _broadcast("stage_start", stage=1, name="Ocean.io", desc="Finding lookalike companies")
        with _state_lock: _state["stage"] = 1

        companies = s1.run(seed_domain, config)
        ckpt.save(run_id, "stage1_companies", companies)

        with _state_lock:
            _state["companies"] = companies
            _state["stages"][1] = "done"
        _broadcast("stage_done", stage=1, count=len(companies), companies=companies)

        if not companies:
            raise RuntimeError("No lookalike companies found for this domain.")

        # ── Stage 2 ──────────────────────────────────────────────────────────
        with _state_lock: _state["stages"][2] = "active"
        _broadcast("stage_start", stage=2, name="Prospeo", desc="Finding decision-makers")

        # Wrap stage2 to emit a contact event after each company is processed
        contacts_so_far: list[dict] = []

        original_s2_run = s2.run
        def _s2_instrumented(companies, config):
            result = original_s2_run(companies, config)
            return result

        contacts = _s2_instrumented(companies, config)
        ckpt.save(run_id, "stage2_contacts", contacts)

        with _state_lock:
            _state["contacts"] = contacts
            _state["stages"][2] = "done"
        _broadcast("stage_done", stage=2, count=len(contacts), contacts=_safe_contacts(contacts))

        if not contacts:
            raise RuntimeError("No decision-maker contacts found.")

        # ── Stage 3 ──────────────────────────────────────────────────────────
        with _state_lock: _state["stages"][3] = "active"
        _broadcast("stage_start", stage=3, name="Eazyreach", desc="Resolving verified emails")

        contacts = s3.run(contacts, config)
        ckpt.save(run_id, "stage3_emails", contacts)

        with _state_lock:
            _state["contacts"] = contacts
            _state["stages"][3] = "done"
        _broadcast("stage_done", stage=3,
                   count=sum(1 for c in contacts if c.get("email")),
                   contacts=_safe_contacts(contacts))

        # ── Stage 4 — confirmation ────────────────────────────────────────────
        sendable = [c for c in contacts if c.get("email")]
        if not sendable:
            _log("No emails resolved — skipping Stage 4.", "warn")
            _broadcast("complete", sent=0, failed=0)
            with _state_lock:
                _state["running"] = False
                _state["done"]    = True
                _state["stages"][4] = "skipped"
            return

        # Ask for confirmation via SSE
        _confirm_event.clear()
        _confirm_answer = False

        with _state_lock:
            _state["confirm_needed"]   = True
            _state["confirm_contacts"] = _safe_contacts(sendable)

        _broadcast("confirm_needed",
                   count=len(sendable),
                   contacts=_safe_contacts(sendable))

        # Wait up to 5 minutes for user confirmation
        confirmed = _confirm_event.wait(timeout=300)
        with _state_lock:
            _state["confirm_needed"] = False

        if not confirmed or not _confirm_answer:
            _log("Send cancelled by user.", "warn")
            _broadcast("confirm_result", approved=False)
            _broadcast("complete", sent=0, failed=0, cancelled=True)
            with _state_lock:
                _state["running"] = False
                _state["done"]    = True
                _state["stages"][4] = "cancelled"
            return

        _broadcast("confirm_result", approved=True)

        # ── Stage 4 ──────────────────────────────────────────────────────────
        with _state_lock: _state["stages"][4] = "active"
        _broadcast("stage_start", stage=4, name="Brevo", desc="Sending personalised emails")

        # Patch stage4 to emit per-send events
        original_send = s4._send_one
        def _instrumented_send(api_key, payload):
            result = original_send(api_key, payload)
            recipient = payload.get("to", [{}])[0].get("email", "")
            name      = payload.get("to", [{}])[0].get("name", "")
            _broadcast("email_sent", email=recipient, name=name,
                       message_id=result.get("messageId",""))
            return result
        s4._send_one = _instrumented_send

        config_no_prompt = {**config, "SKIP_SEND_CONFIRM": "true"}
        contacts = s4.run(contacts, config_no_prompt)
        ckpt.save(run_id, "stage4_sent", contacts)

        sent   = sum(1 for c in contacts if c.get("send_status") == "SENT")
        failed = sum(1 for c in contacts if (c.get("send_status","")).startswith("FAILED"))

        with _state_lock:
            _state["contacts"] = contacts
            _state["stages"][4] = "done"
            _state["sent"]   = sent
            _state["failed"] = failed

        _broadcast("stage_done", stage=4, sent=sent, failed=failed)
        _broadcast("complete", sent=sent, failed=failed)

    except Exception as exc:
        tb = traceback.format_exc()
        _log(f"Pipeline error: {exc}", "error")
        _broadcast("error", message=str(exc), traceback=tb)
        with _state_lock:
            _state["error"] = str(exc)
    finally:
        with _state_lock:
            _state["running"] = False
            _state["done"]    = True


def _safe_contacts(contacts: list) -> list:
    """Return a minimal safe subset of contact data for the UI."""
    safe = []
    for c in contacts:
        safe.append({
            "full_name":     c.get("full_name", ""),
            "job_title":     c.get("job_title", ""),
            "company_name":  c.get("company_name", ""),
            "company_domain":c.get("company_domain", ""),
            "email":         c.get("email", ""),
            "email_status":  c.get("email_status", ""),
            "send_status":   c.get("send_status", ""),
            "message_id":    c.get("message_id", ""),
        })
    return safe


# ── Flask routes ──────────────────────────────────────────────────────────────

@app.route("/")
def index():
    from dashboard.template import HTML
    return HTML

@app.route("/state")
def state():
    with _state_lock:
        snap = dict(_state)
    return jsonify(snap)

@app.route("/run", methods=["POST"])
def run_pipeline():
    body = request.get_json(silent=True) or {}
    seed = (body.get("domain") or "").strip().lower()
    if not seed:
        return jsonify({"error": "domain required"}), 400

    with _state_lock:
        if _state["running"]:
            return jsonify({"error": "Pipeline already running"}), 409

    # Build config from env
    config = {}
    for key in ("OCEAN_API_KEY","PROSPEO_API_KEY","EAZYREACH_API_KEY",
                "BREVO_API_KEY","SENDER_EMAIL","SENDER_NAME",
                "OCEAN_LOOKALIKE_COUNT","PROSPEO_MAX_PER_COMPANY"):
        val = os.getenv(key, "")
        if val:
            config[key] = val

    # Override from request body if provided
    for key in ("count", "max_per_company"):
        if body.get(key):
            env_key = "OCEAN_LOOKALIKE_COUNT" if key == "count" else "PROSPEO_MAX_PER_COMPANY"
            config[env_key] = str(body[key])

    # Reset state
    with _state_lock:
        _state.update({
            "running": True, "done": False, "error": None, "stage": 0,
            "stages": {1:"idle", 2:"idle", 3:"idle", 4:"idle"},
            "companies": [], "contacts": [], "sent": 0, "failed": 0,
            "seed": seed, "confirm_needed": False, "confirm_contacts": [], "logs": [],
        })

    t = threading.Thread(target=_run_pipeline, args=(seed, config), daemon=True)
    t.start()
    return jsonify({"status": "started", "seed": seed})

@app.route("/confirm", methods=["POST"])
def confirm_send():
    global _confirm_answer
    body = request.get_json(silent=True) or {}
    _confirm_answer = bool(body.get("approved", False))
    _confirm_event.set()
    return jsonify({"status": "ok", "approved": _confirm_answer})

@app.route("/events")
def events():
    q: queue.Queue = queue.Queue(maxsize=500)
    with _queues_lock:
        _client_queues.append(q)

    # Send current state snapshot to newly connected client
    with _state_lock:
        snap = dict(_state)
    q.put_nowait(json.dumps({"type": "state_snapshot", "state": snap}))

    @stream_with_context
    def generate():
        try:
            while True:
                try:
                    payload = q.get(timeout=25)
                    yield f"data: {payload}\n\n"
                except queue.Empty:
                    # Heartbeat to keep connection alive
                    yield "data: {\"type\":\"ping\"}\n\n"
        except GeneratorExit:
            pass
        finally:
            with _queues_lock:
                try:
                    _client_queues.remove(q)
                except ValueError:
                    pass

    return Response(
        generate(),
        mimetype="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no",
            "Connection": "keep-alive",
        },
    )


def start_server(host: str = "127.0.0.1", port: int = 5055, open_browser: bool = True):
    import webbrowser
    url = f"http://{host}:{port}"
    if open_browser:
        # Slight delay so Flask is ready before browser opens
        threading.Timer(1.2, lambda: webbrowser.open(url)).start()
    print(f"\n  🌐  Dashboard running at {url}\n  Press Ctrl+C to stop.\n")
    app.run(host=host, port=port, debug=False, use_reloader=False, threaded=True)