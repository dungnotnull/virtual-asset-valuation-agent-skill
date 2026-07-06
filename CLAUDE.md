# CLAUDE.md - Virtual Asset / Digital Item Valuation (NFT / game / domain)

**Skill slug:** `virtual-asset-valuation`
**Source idea:** #180 (Vietnamese backlog `ideas.md`)
**Cluster:** finance-insurance - Finance, Investment and Insurance
**Tagline:** Value NFTs, game accounts, and domains using comparables, liquidity, and rarity models.
**Current phase:** Phase 5 - Integration and Cross-Skill Wiring (all phases 0-5 complete).

## Problem This Skill Solves
Owners and buyers of NFTs, game accounts, and domain names have no defensible way to price illiquid, idiosyncratic digital assets. This skill values an asset using intangible-asset valuation methods, comparable-sales analysis, and rarity/liquidity scoring, and continuously refreshes marketplace transaction data.

## Harness Flow (Summary)
1. **Intake** -> `sub-profile-intake` gathers inputs and frames the problem.
2. **Screen / select** -> `sub-risk-screener` selects the governing framework and screens risk/scope; computes a composite discount.
3. **Knowledge refresh** -> optional `tools/knowledge_updater.py` keeps `SECOND-KNOWLEDGE-BRAIN.md` current.
4. **Market data** -> `sub-market-data-updater` refreshes floor/liquidity.
5. **Score / analyze** -> `sub-scoring-engine` scores >=2 named frameworks and triangulates a value band.
6. **Gate** -> evidence + framework + challenge gates must pass (`tools/vav/gates.py`).
7. **Synthesize** -> main harness emits the scored deliverable + prioritized improvement roadmap.

## Sub-skills
- `skills/sub-profile-intake.md` - Capture the asset type, identifiers, provenance, utility, and valuation purpose.
- `skills/sub-risk-screener.md` - Screen platform, custody, wash-trading, and regulatory risks that adjust value.
- `skills/sub-scoring-engine.md` - Triangulate value via comparables, rarity, and income; produce a value range with confidence.
- `skills/sub-market-data-updater.md` - Refresh marketplace transaction history, floor prices, and liquidity metrics.
- `skills/sub-improvement-roadmap.md` - Recommend actions to realize or protect value (timing, listing strategy, custody).

## Tools Required
WebSearch, WebFetch, Read, Write, Bash

## Knowledge Sources (for crawl + reasoning)
- NFT marketplace data (OpenSea, Blur, Magic Eden public stats)
- Domain sales comparables (NameBio, Dan.com, GoDaddy auctions)
- Game-asset marketplaces and trade indices
- IVS 104 / RICS Red Book / USPAP / AICPA SSVS intangible-asset valuation standards
- ArXiv (q-fin.PR, econ.GN) and Google Scholar for digital-asset pricing research

## Supporting Python Tools
- `tools/knowledge_updater.py` - ArXiv + crawl4ai pipeline that fetches latest papers/reports from the domain sources above, scores by recency + relevance, deduplicates by URL/DOI hash, and appends to `SECOND-KNOWLEDGE-BRAIN.md`. Recommended schedule: weekly cron. Idempotent; graceful offline no-op.
- `tools/vav/` - dependency-free core package: `schemas.py` (typed dataclasses + validators), `gates.py` (evidence/framework/challenge gates), `scoring.py` (comparables/income/rarity/liquidity/triangulation), `risk.py` (wash-trade + risk vectors + discount), `marketdata.py` (snapshots + aggregate), `knowledge.py` (brain helpers), `harness.py` (orchestration + offline dry-run).
- `skills/schemas/` - canonical JSON schemas (`valuation_schema.json`, `gate_schema.json`) shared across the cluster.

## How to validate (offline)
```
python -m pytest tests -q
```
All 6 scenario fixtures pass `vav.harness.run_dry` and `vav.gates.run_all_gates`.

## Reference Docs (this folder)
- `PROJECT-detail.md` - full technical spec
- `PROJECT-DEVELOPMENT-PHASE-TRACKING.md` - phase roadmap (all phases 0-5 complete)
- `SECOND-KNOWLEDGE-BRAIN.md` - self-improving knowledge base
- `skills/main.md` - harness entry point
- `skills/CLUSTER-SHARED.md` - cluster cross-skill wiring (Phase 5)
