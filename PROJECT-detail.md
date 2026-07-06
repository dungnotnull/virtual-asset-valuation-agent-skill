# PROJECT-detail.md - Virtual Asset / Digital Item Valuation (NFT / game / domain)

## Executive Summary
This skill is a full Claude harness that values NFTs, game accounts, and domains using comparables, liquidity, and rarity models. It operates research-first: every material judgment is grounded in a named, citable framework and, where possible, a freshly retrieved source. It produces a professional-grade deliverable: a multi-dimensional score against the chosen framework plus a prioritized, effort/impact-ranked improvement roadmap. The deterministic contract is implemented in `tools/vav` and validated by `tests/`.

## Problem Statement
Owners and buyers of NFTs, game accounts, and domain names have no defensible way to price illiquid, idiosyncratic digital assets. This skill values an asset using intangible-asset valuation methods, comparable-sales analysis, and rarity/liquidity scoring, and continuously refreshes marketplace transaction data.

## Target Users and Use Cases
Primary users are practitioners and decision-makers in the Finance, Investment and Insurance domain. Trigger examples:
1. User wants a domain appraised; skill triangulates comparables, length, and keyword value into a range.
2. An NFT's rarity is unclear; skill computes statistical rarity and compares to collection floor.
3. A game account is for sale; skill values it from comparable account sales and progression utility.
4. Wash-trading inflates an NFT's history; risk screener discounts manipulated comparables.
5. Market data shifts; updater refreshes floor/liquidity and re-prices the asset.
6. Owner asks the best time to sell; roadmap recommends listing strategy and timing.

## Harness Architecture
```
/virtual-asset-valuation (skills/main.md harness)
  -> sub-profile-intake              [intake / framing]        -> AssetProfile
  -> sub-risk-screener              [framework / risk screen]  -> RiskScreen (+ composite_discount)
  -> knowledge refresh   [SECOND-KNOWLEDGE-BRAIN via tools/knowledge_updater.py]
  -> sub-market-data-updater        [market data refresh]     -> MarketDataSnapshot[]
  -> sub-scoring-engine             [multi-dim scoring]       -> ScoredDimension[]
  -> evidence + framework + challenge gate (tools/vav/gates.py)
  -> sub-improvement-roadmap        [prioritized effort x impact] -> RoadmapItem[]
  -> SYNTHESIZE          -> ValuationReport (skills/schemas/valuation_schema.json)
```

## Full Sub-Skill Catalog
### sub-profile-intake
- **Purpose:** Capture the asset type, identifiers, provenance, utility, and the valuation purpose.
- **Inputs:** user context + prior stage output.
- **Outputs:** `AssetProfile` (typed; see `valuation_schema.json`).
- **Tools:** WebSearch, WebFetch, Read, Write, Bash.
- **Quality gate:** schema-valid; required fields per asset_type; refuse out-of-scope.

### sub-risk-screener
- **Purpose:** Screen platform, custody, wash-trading, and regulatory risks; compute composite discount.
- **Inputs:** `AssetProfile` + on-chain history (optional).
- **Outputs:** `RiskScreen` (typed; see `valuation_schema.json`).
- **Tools:** WebSearch, WebFetch, Read, Write, Bash.
- **Quality gate:** schema-valid; all vectors in [0,1]; framework = `risk_discounting_platform_custody_regulatory`.

### sub-scoring-engine
- **Purpose:** Triangulate value via >=2 named frameworks; produce a value range with confidence.
- **Inputs:** `AssetProfile`, `RiskScreen`, refreshed market data.
- **Outputs:** list of `ScoredDimension` (typed).
- **Tools:** WebSearch, WebFetch, Read, Write, Bash.
- **Quality gate:** >=2 distinct frameworks; >=1 evidence per dimension at tier >= field_study.

### sub-market-data-updater
- **Purpose:** Refresh marketplace transaction history, floor prices, and liquidity metrics.
- **Inputs:** `AssetProfile` (identifiers, asset_type).
- **Outputs:** list of `MarketDataSnapshot` + composite.
- **Tools:** WebSearch, WebFetch, Read, Write, Bash.
- **Quality gate:** snapshots schema-valid; composite via `aggregate`; staleness noted.

### sub-improvement-roadmap
- **Purpose:** Recommend actions to realize or protect value (timing, listing strategy, custody).
- **Inputs:** full in-progress report.
- **Outputs:** list of `RoadmapItem` ranked by priority = impact*10 - effort.
- **Tools:** WebSearch, WebFetch, Read, Write, Bash.
- **Quality gate:** schema-valid; effort/impact in [1,5]; sorted by priority desc.

## Skill File Format Specification
Every skill file uses YAML frontmatter (`name`, `description`) followed by the required sections: Role and Persona, Inputs, Procedure, Output, Tools, Quality Gate. The main harness invokes sub-skills in the order shown in the architecture above. Typed contracts are in `skills/schemas/` and `tools/vav`.

## E2E Execution Flow
1. Parse the user request; if inputs are insufficient, `sub-profile-intake` asks targeted intake questions.
2. `sub-risk-screener` selects the governing framework and screens scope/risk; refuse/disclaim if out of scope.
3. Refresh knowledge if the brain is stale (>7 days) and WebSearch/WebFetch are available; otherwise degrade gracefully with a stated limitation.
4. `sub-market-data-updater` refreshes floor/liquidity.
5. `sub-scoring-engine` scores each dimension, citing evidence per claim; drops wash-trade-flagged comparables.
6. Run the evidence/quality gates and a devil's-advocate challenge pass (`vav.gates.run_all_gates`).
7. Emit the scored report + roadmap as a `ValuationReport` (Output Format below).

## SECOND-KNOWLEDGE-BRAIN Integration
- **Sources:** NFT marketplaces; domain sales comparables; game-asset marketplaces; IVS/RICS/USPAP/AICPA standards; ArXiv (q-fin.PR, econ.GN) and Google Scholar.
- **Crawl config:** `tools/knowledge_updater.py` (CLI: `--since`, `--max`, `--dry-run`, `--brain`, `--no-arxiv`, `--no-crawl`).
- **Append format:** date-stamped entries with Title, Authors, Year, Venue, DOI/URL, score; deduplicated by URL/DOI hash (idempotent).

## Quality Gates
- **Evidence gate:** every material claim is traceable to a cited source at tier >= field_study; >=1 evidence per scored dimension; marketplace facts at `primary_market_data`.
- **Framework gate:** all scoring is grounded in the named frameworks (see `skills/main.md`); >=2 distinct frameworks (triangulation).
- **Challenge gate:** >=2 substantive devil's-advocate challenges.
- Machine contract: `skills/schemas/gate_schema.json` + `tools/vav/gates.py`.

## Test Scenarios
See `tests/test-scenarios.md` and the machine fixtures in `tests/fixtures/scenario_*.json` (validated by `tests/`).

## Key Design Decisions
1. Framework-grounded scoring only - no ad-hoc rubrics.
2. Research-first with graceful degradation when offline (`confidence_band(..., online=False)`).
3. Composable sub-skills (5) reusable by cluster siblings (see `skills/CLUSTER-SHARED.md`).
4. Deliverable is an artifact (`ValuationReport`), not a chat reply.
5. Evidence/quality gates enforced before any sensitive/regulated output.
6. Dependency-free core (`tools/vav`), stdlib-only, for portable CI and open-source use.
