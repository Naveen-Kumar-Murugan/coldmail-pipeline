"""
utils/checkpoint.py
───────────────────
Persist pipeline progress to disk so a crash mid-run can be resumed.

Layout
------
    data/runs/<run_id>/
        stage1_companies.json
        stage2_contacts.json
        stage3_emails.json
        stage4_sent.json
        meta.json              ← run metadata (seed domain, timestamps)
"""

import json
import time
from pathlib import Path
from typing import Any

from utils.logger import log

_RUNS_DIR = Path(__file__).parent.parent / "data" / "runs"


def _run_dir(run_id: str) -> Path:
    d = _RUNS_DIR / run_id
    d.mkdir(parents=True, exist_ok=True)
    return d


def save(run_id: str, stage: str, data: Any) -> None:
    """Atomically write stage output to disk."""
    path = _run_dir(run_id) / f"{stage}.json"
    tmp = path.with_suffix(".tmp")
    tmp.write_text(json.dumps(data, indent=2, ensure_ascii=False))
    tmp.replace(path)
    log.debug("Checkpoint saved: %s", path)


def load(run_id: str, stage: str) -> Any | None:
    """Return saved stage data, or None if not yet written."""
    path = _run_dir(run_id) / f"{stage}.json"
    if path.exists():
        try:
            return json.loads(path.read_text())
        except json.JSONDecodeError:
            return None
    return None


def exists(run_id: str, stage: str) -> bool:
    return (_run_dir(run_id) / f"{stage}.json").exists()


def save_meta(run_id: str, seed_domain: str) -> None:
    meta = {
        "run_id": run_id,
        "seed_domain": seed_domain,
        "started_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
    }
    save(run_id, "meta", meta)


def list_runs() -> list[str]:
    """Return all run IDs found in data/runs/, newest first."""
    if not _RUNS_DIR.exists():
        return []
    dirs = sorted(
        (d.name for d in _RUNS_DIR.iterdir() if d.is_dir()),
        reverse=True,
    )
    return dirs


def new_run_id(seed_domain: str) -> str:
    """Generate a timestamped run ID from the seed domain."""
    ts = time.strftime("%Y%m%d_%H%M%S")
    safe = seed_domain.replace(".", "_").replace("/", "_")
    return f"{ts}_{safe}"