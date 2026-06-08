"""
pipeline/stage4_brevo.py
Stage 4 · Brevo — Send Personalised Outreach Emails

API: POST https://api.brevo.com/v3/smtp/email
Auth header: api-key: <BREVO_API_KEY>
"""
import os
from typing import Any
import requests
from utils.logger import stage_header, ok, warn, err, info, console, _RICH
from utils.rate_limiter import raise_for_rate_limit, sleep_between, retry_request
from email_templates.outreach import build_email

_BREVO_URL = "https://api.brevo.com/v3/smtp/email"


@retry_request
def _send_one(api_key: str, payload: dict) -> dict:
    resp = requests.post(
        _BREVO_URL,
        headers={"api-key": api_key, "content-type": "application/json", "accept": "application/json"},
        json=payload,
        timeout=30,
    )
    raise_for_rate_limit(resp)
    resp.raise_for_status()
    return resp.json()


def _dedup(contacts: list[dict]) -> tuple[list[dict], int]:
    seen: set[str] = set(); clean = []; dupes = 0
    for c in contacts:
        e = (c.get("email") or "").strip().lower()
        if not e: continue
        if e in seen: dupes += 1; continue
        seen.add(e); clean.append(c)
    return clean, dupes


def _safety_checkpoint(contacts: list[dict]) -> bool:
    if _RICH:
        from rich.table import Table
        from rich.panel import Panel
        tbl = Table(show_lines=False, border_style="dim", padding=(0, 1))
        tbl.add_column("#", style="dim", width=3)
        tbl.add_column("Name", style="bold")
        tbl.add_column("Title", style="cyan")
        tbl.add_column("Company")
        tbl.add_column("Email", style="green")
        for i, c in enumerate(contacts, 1):
            tbl.add_row(str(i), c.get("full_name") or "—", c.get("job_title") or "—",
                        c.get("company_name") or "—", c.get("email") or "—")
        console.print(Panel(tbl,
            title=f"[bold yellow]⚠  READY TO SEND — {len(contacts)} email(s)[/bold yellow]",
            border_style="yellow", padding=(1, 2)))
        answer = console.input("[bold yellow]Proceed and send? [y/N] [/bold yellow]")
    else:
        print(f"\n{'='*60}")
        print(f"  ⚠  READY TO SEND — {len(contacts)} email(s)")
        print(f"{'='*60}")
        print(f"  {'#':>3}  {'Name':<25}  {'Email':<35}  Title")
        for i, c in enumerate(contacts, 1):
            print(f"  {i:>3}  {c.get('full_name',''):<25}  {c.get('email',''):<35}  {c.get('job_title','')}")
        print(f"{'='*60}")
        answer = input("  Proceed and send all emails? [y/N]: ")
    return answer.strip().lower() in ("y", "yes")


def run(contacts: list[dict], config: dict) -> list[dict[str, Any]]:
    stage_header(4, "Brevo", "Sending personalised outreach emails")

    api_key      = config.get("BREVO_API_KEY") or os.getenv("BREVO_API_KEY", "")
    sender_email = config.get("SENDER_EMAIL")  or os.getenv("SENDER_EMAIL", "naveenkumarm@navdev.xyz")
    sender_name  = config.get("SENDER_NAME")   or os.getenv("SENDER_NAME", "Naveen from NavDev")

    if not api_key:     
        err("BREVO_API_KEY is missing.")
        return []
    if not sender_email: 
        err("SENDER_EMAIL sender email is missing.")
        return []

    sendable = [c for c in contacts if c.get("email")]
    if not sendable:
        warn("Stage 4: No contacts with emails."); return contacts

    sendable, dupes = _dedup(sendable)
    if dupes: warn(f"Removed {dupes} duplicate email(s).")

    skip_confirm = str(config.get("SKIP_SEND_CONFIRM", "false")).lower() == "true"
    if not skip_confirm:
        if not _safety_checkpoint(sendable):
            warn("Send cancelled. No emails sent.")
            for c in contacts: c.setdefault("send_status", "CANCELLED")
            return contacts
    else:
        info("SKIP_SEND_CONFIRM=true — bypassing confirmation.")

    sent = failed = 0
    total = len(sendable)

    for idx, contact in enumerate(sendable, 1):
        name  = contact.get("full_name") or "—"
        email = contact["email"]
        info(f"[{idx}/{total}] Sending to {name} <{email}> …")

        try:
            copy = build_email(contact, sender_name)
            payload = {
                "sender":      {"name": sender_name, "email": sender_email},
                "to":          [{"email": email, "name": name}],
                "replyTo":     {"email": sender_email},
                "subject":     copy["subject"],
                "htmlContent": copy["html_body"],
                "textContent": copy["text_body"],
                "tags":        ["vocallabs-pipeline"],
            }
            result = _send_one(api_key, payload)
            contact["send_status"] = "SENT"
            contact["message_id"]  = result.get("messageId", "")
            sent += 1; info(f"sent ✓")
        except requests.HTTPError as exc:
            sc = exc.response.status_code if exc.response else "?"
            body = {}
            try: body = exc.response.json()
            except Exception: pass
            msg = body.get("message", "")
            if sc == 401:
                err("Brevo: Invalid API key. Stopping."); contact["send_status"] = "FAILED:AUTH"
                failed += 1; break
            warn(f"Brevo HTTP {sc}: {msg}")
            contact["send_status"] = f"FAILED:HTTP_{sc}"; failed += 1; warn("failed.")
        except Exception as exc:
            contact["send_status"] = "FAILED:EXCEPTION"; failed += 1; err(f"error: {exc}")

        sleep_between(0.3)

    for c in contacts:
        c.setdefault("send_status", "SKIPPED_NO_EMAIL")

    ok(f"Stage 4 complete — {sent} sent, {failed} failed.")
    _print_summary(contacts)
    return contacts


def _print_summary(contacts: list[dict]) -> None:
    if _RICH:
        from rich.table import Table
        tbl = Table(title="Send Summary", show_lines=False, border_style="dim")
        tbl.add_column("#", style="dim", width=3)
        tbl.add_column("Name", style="bold")
        tbl.add_column("Email", style="cyan")
        tbl.add_column("Status")
        tbl.add_column("Message ID", style="dim")
        for i, c in enumerate(contacts, 1):
            s = c.get("send_status", "—")
            if s == "SENT": s_str = "[green]SENT[/green]"
            elif s == "SKIPPED_NO_EMAIL": s_str = "[dim]NO EMAIL[/dim]"
            elif s == "CANCELLED": s_str = "[yellow]CANCELLED[/yellow]"
            elif s and s.startswith("FAILED"): s_str = f"[red]{s}[/red]"
            else: s_str = s
            tbl.add_row(str(i), c.get("full_name") or "—", c.get("email") or "—",
                        s_str, c.get("message_id") or "—")
        console.print(tbl)
    else:
        info(f"\n  {'#':>3}  {'Name':<25}  {'Email':<35}  Status")
        for i, c in enumerate(contacts, 1):
            info(f"  {i:>3}  {c.get('full_name',''):<25}  "
                  f"{c.get('email','—'):<35}  {c.get('send_status','—')}")