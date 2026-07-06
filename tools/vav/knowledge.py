"""Knowledge-brain helpers shared by `tools/knowledge_updater.py` and the harness.

Pure helpers over `SECOND-KNOWLEDGE-BRAIN.md`: hashing entries, reading existing
hashes, appending deduplicated rows, and measuring staleness. No external deps.
"""
from __future__ import annotations

import datetime
import hashlib
import os
import re
from typing import Iterable, List, Sequence, Set

BRAIN_DEFAULT = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "..", "..", "SECOND-KNOWLEDGE-BRAIN.md")
)

HASH_TAG_RE = re.compile(r"<!--h:([0-9a-f]{12})-->")
UPDATE_LOG_RE = re.compile(r"^\s*-\s*(\d{4}-\d{2}-\d{2})\b", re.M)


def entry_hash(url: str, title: str = "") -> str:
    """Stable 12-hex-char identity for dedup (URL preferred, title fallback)."""
    key = (url or "").strip().lower()
    if not key:
        key = (title or "").strip().lower()
    return hashlib.sha1(key.encode("utf-8", "ignore")).hexdigest()[:12]


def read_brain_hashes(path: str = BRAIN_DEFAULT) -> Set[str]:
    if not os.path.exists(path):
        return set()
    with open(path, encoding="utf-8") as fh:
        return set(HASH_TAG_RE.findall(fh.read()))


def brain_staleness_days(path: str = BRAIN_DEFAULT) -> int:
    """Days since the last Knowledge Update Log entry. Large if never updated."""
    if not os.path.exists(path):
        return 10**9
    with open(path, encoding="utf-8") as fh:
        txt = fh.read()
    dates = UPDATE_LOG_RE.findall(txt)
    if not dates:
        return 10**9
    latest = max(dates)
    try:
        d = datetime.date.fromisoformat(latest)
    except ValueError:
        return 10**9
    return (datetime.date.today() - d).days


class Brain:
    """Thin handle around the brain markdown file."""

    def __init__(self, path: str = BRAIN_DEFAULT):
        self.path = path

    def exists(self) -> bool:
        return os.path.exists(self.path)

    def hashes(self) -> Set[str]:
        return read_brain_hashes(self.path)

    def staleness_days(self) -> int:
        return brain_staleness_days(self.path)

    def is_stale(self, threshold_days: int = 7) -> bool:
        return self.staleness_days() > threshold_days


def append_entries(entries: Sequence[dict], path: str = BRAIN_DEFAULT,
                   today: datetime.date | None = None) -> List[dict]:
    """Append deduplicated, date-stamped rows to the brain. Returns added entries.

    Each entry dict must have: title, authors, date, url, abstract, score(optional).
    Idempotent: re-running with the same entries adds nothing.
    """
    if not entries:
        return []
    today = today or datetime.date.today()
    existing = read_brain_hashes(path)
    added: List[dict] = []
    rows: List[str] = []
    logs: List[str] = []
    for e in entries:
        key = entry_hash(e.get("url", ""), e.get("title", ""))
        if key in existing:
            continue
        existing.add(key)
        title = (e.get("title") or "")[:90].replace("|", "/")
        authors = (e.get("authors") or "-")[:40]
        year = (e.get("date") or "-")[:4]
        url = e.get("url") or "-"
        score = e.get("score", 0.0)
        rows.append(
            "| {t} | {a} | {y} | ArXiv/Web | {u} | score={s:.2f} <!--h:{h}--> |".format(
                t=title, a=authors, y=year, u=url, s=float(score), h=key)
        )
        logs.append("- %s - added: %s" % (today.isoformat(), title))
        added.append(e)
    if not rows:
        return []
    with open(path, "a", encoding="utf-8") as fh:
        fh.write("\n<!-- auto-appended %s -->\n" % today.isoformat())
        fh.write("\n".join(rows) + "\n")
        fh.write("\n## Knowledge Update Log (auto)\n")
        fh.write("\n".join(logs) + "\n")
    return added
