# -*- coding: utf-8 -*-
"""knowledge_updater.py - self-improving knowledge pipeline for the
`virtual-asset-valuation` skill.

Pipeline (per CLAUDE.md / PROJECT-detail.md):
  1. ArXiv Atom API -> latest papers from configured categories
  2. crawl4ai (optional) -> authoritative domain pages
  3. parse -> title, authors, date, DOI/URL, abstract, key findings
  4. score -> recency + domain-keyword relevance
  5. append -> scored, deduplicated, date-stamped entries to SECOND-KNOWLEDGE-BRAIN.md
  6. dedupe -> skip entries whose URL/DOI hash already exists (idempotent)

Designed to degrade gracefully: if the network or crawl4ai is unavailable it
logs and no-ops rather than corrupting the brain. Idempotent: re-running with the
same upstream data adds nothing new.

Usage:
  python tools/knowledge_updater.py [--since YYYY-MM-DD] [--max N] [--dry-run]
                                    [--brain PATH] [--no-arxiv] [--no-crawl]

Recommended schedule: weekly cron.
"""
from __future__ import annotations

import argparse
import datetime
import json
import logging
import os
import re
import sys
import urllib.parse
import urllib.request

# Make `vav` importable when run as a script.
sys.path.insert(0, os.path.join(os.path.dirname(__file__)))
from vav.knowledge import Brain, append_entries, entry_hash  # noqa: E402

LOG = logging.getLogger("knowledge_updater")

BRAIN_DEFAULT = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "..", "SECOND-KNOWLEDGE-BRAIN.md")
)

ARXIV_CATEGORIES = ["q-fin.PR", "econ.GN"]
SEARCH_QUERIES = [
    "NFT valuation rarity liquidity",
    "domain name appraisal model",
    "intangible digital asset pricing",
    "virtual goods secondary market",
]
DOMAINS = ["namebio.com", "opensea.io", "blur.io"]
KEYWORDS = sorted({w.lower() for q in SEARCH_QUERIES for w in q.split()})

USER_AGENT = "vav-knowledge-updater/1.0 (+virtual-asset-valuation skill)"


def _setup_logging(verbose: bool) -> None:
    logging.basicConfig(
        level=logging.DEBUG if verbose else logging.INFO,
        format="%(asctime)s %(levelname)s %(name)s: %(message)s",
    )


def relevance(entry: dict) -> float:
    """Score = recency weight + keyword-match density."""
    text = (entry.get("title", "") + " " + entry.get("abstract", "")).lower()
    kw_hits = sum(1 for k in KEYWORDS if k in text)
    date_str = (entry.get("date") or "")[:10]
    try:
        d = datetime.date.fromisoformat(date_str)
        age_days = (datetime.date.today() - d).days
        recency = max(0.0, 1.0 - age_days / 730.0)  # 2-year decay
    except ValueError:
        recency = 0.0
    return float(kw_hits) + 2.0 * recency


def fetch_arxiv(category: str, max_results: int = 15, since: datetime.date | None = None) -> list:
    """Query the ArXiv Atom API for a category. Returns list of entry dicts."""
    base = "http://export.arxiv.org/api/query"
    params = {
        "search_query": "cat:" + category,
        "sortBy": "submittedDate",
        "sortOrder": "descending",
        "max_results": str(max_results),
    }
    url = base + "?" + urllib.parse.urlencode(params)
    req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            data = resp.read().decode("utf-8", "ignore")
    except Exception as exc:
        LOG.warning("arxiv fetch failed for %s: %s", category, exc)
        return []
    entries = []
    for block in re.findall(r"<entry>(.*?)</entry>", data, re.S):
        def g(tag: str) -> str:
            m = re.search(r"<%s>(.*?)</%s>" % (tag, tag), block, re.S)
            return re.sub(r"\s+", " ", m.group(1)).strip() if m else ""
        title = g("title")
        summary = g("summary")
        published = g("published")[:10]
        link = ""
        m = re.search(r"<id>(.*?)</id>", block, re.S)
        if m:
            link = m.group(1).strip()
        authors = ", ".join(re.findall(r"<name>(.*?)</name>", block))
        if title and (since is None or _parse_date(published) >= since):
            entries.append({
                "title": title, "authors": authors, "date": published,
                "url": link, "abstract": summary, "score": 0.0,
            })
    return entries


def _parse_date(s: str) -> datetime.date:
    try:
        return datetime.date.fromisoformat(s[:10])
    except ValueError:
        return datetime.date.min


def crawl4ai_domains(domains=DOMAINS) -> list:
    """Optional: use crawl4ai to pull authoritative domain pages. No-op if absent."""
    try:
        from crawl4ai import WebCrawler  # type: ignore
    except Exception:
        LOG.info("crawl4ai not installed; skipping domain crawl (graceful degradation).")
        return []
    out = []
    crawler = WebCrawler()
    crawler.warmup()
    for d in domains:
        try:
            res = crawler.run(url="https://" + d)
            out.append({
                "title": "Domain scan: " + d, "authors": "",
                "date": str(datetime.date.today()),
                "url": "https://" + d,
                "abstract": (getattr(res, "markdown", "") or "")[:400],
                "score": 0.0,
            })
        except Exception as exc:
            LOG.warning("crawl4ai failed for %s: %s", d, exc)
    return out


def collect(args: argparse.Namespace) -> list:
    entries: list = []
    since = datetime.date.fromisoformat(args.since) if args.since else None
    if not args.no_arxiv:
        for cat in ARXIV_CATEGORIES:
            entries += fetch_arxiv(cat, max_results=args.max, since=since)
    if not args.no_crawl:
        entries += crawl4ai_domains()
    for e in entries:
        e["score"] = relevance(e)
    entries.sort(key=lambda e: e["score"], reverse=True)
    return entries


def main(argv: list | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--since", help="only include items dated on/after YYYY-MM-DD")
    parser.add_argument("--max", type=int, default=15, help="max results per source")
    parser.add_argument("--dry-run", action="store_true", help="print what would be appended")
    parser.add_argument("--brain", default=BRAIN_DEFAULT, help="path to SECOND-KNOWLEDGE-BRAIN.md")
    parser.add_argument("--no-arxiv", action="store_true", help="skip ArXiv fetch")
    parser.add_argument("--no-crawl", action="store_true", help="skip crawl4ai domain crawl")
    parser.add_argument("-v", "--verbose", action="store_true", help="debug logging")
    args = parser.parse_args(argv)
    _setup_logging(args.verbose)

    brain = Brain(args.brain)
    if not brain.exists():
        LOG.warning("brain file not found at %s; nothing to append to.", args.brain)
        # Not an error: still report collected entries in dry-run.
    entries = collect(args)
    LOG.info("collected %d candidate entries", len(entries))
    if not entries:
        LOG.info("nothing fetched (offline?). Brain left unchanged.")
        return 0
    existing = brain.hashes() if brain.exists() else set()
    fresh = [e for e in entries if entry_hash(e.get("url", ""), e.get("title", "")) not in existing]
    LOG.info("%d fresh entries after dedupe", len(fresh))
    if args.dry_run:
        print(json.dumps(fresh, indent=2, ensure_ascii=False))
        return 0
    if not fresh:
        LOG.info("no new entries to append.")
        return 0
    added = append_entries(fresh, path=args.brain)
    LOG.info("appended %d new entries to %s", len(added), args.brain)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
