"""
utils/logger.py
Rich-powered console logger with graceful fallback to plain print.
"""
import logging
import sys

try:
    from rich.console import Console
    from rich.theme import Theme
    _THEME = Theme({
        "stage":     "bold cyan",
        "success":   "bold green",
        "warning":   "bold yellow",
        "error":     "bold red",
        "dim_info":  "dim white",
        "highlight": "bold magenta",
    })
    console = Console(theme=_THEME, highlight=False)
    _RICH = True
except ImportError:
    console = None
    _RICH = False

logging.basicConfig(level=logging.WARNING, format="%(message)s")
log = logging.getLogger("pipeline")
log.setLevel(logging.DEBUG)


def _p(msg: str) -> None:
    if _RICH:
        console.print(msg)
    else:
        import re
        clean = re.sub(r'\[/?[^\]]+\]', '', msg)
        print(clean)


def stage_header(number: int, name: str, subtitle: str = "") -> None:
    sep = "─" * 60
    _p(f"\n{sep}")
    _p(f"  Stage {number} · {name}" + (f"  {subtitle}" if subtitle else ""))
    _p(sep)


def ok(msg: str)   -> None: _p(f"  ✓  {msg}")
def warn(msg: str) -> None: _p(f"  ⚠  {msg}")
def err(msg: str)  -> None: _p(f"  ✗  {msg}")
def info(msg: str) -> None: _p(f"  ·  {msg}")