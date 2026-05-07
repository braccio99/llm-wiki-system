"""Append-only logger for log.md (Karpathy pattern)."""

from pathlib import Path
from datetime import datetime

LOG_PATH = Path(__file__).resolve().parent.parent.parent / "log.md"


def log_event(kind: str, details: str) -> None:
    """Append a timestamped entry to log.md.

    kind: 'ingest' | 'query' | 'lint'
    details: free-form markdown body (one or more lines).
    """
    ts = datetime.now().strftime("%Y-%m-%d %H:%M")
    entry = f"\n## {ts} — {kind}\n{details.rstrip()}\n"
    if not LOG_PATH.exists():
        LOG_PATH.write_text("# Log\n", encoding="utf-8")
    with LOG_PATH.open("a", encoding="utf-8") as f:
        f.write(entry)
