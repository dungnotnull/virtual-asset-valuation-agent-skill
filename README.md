# Virtual Asset Valuation Agent Skill

> Value NFTs, game accounts, and domain names using comparables, liquidity, and
> rarity models - grounded in named, citable valuation frameworks.

`virtual-asset-valuation` is a research-first Claude skill that produces a
professional-grade valuation artifact for illiquid, idiosyncratic digital assets.
Every material judgment is grounded in a named governing framework, every score
cites its evidence, and every deliverable is validated by deterministic quality
gates before it is shown.

- **Cluster:** finance-insurance (Finance, Investment and Insurance)
- **Asset classes:** NFTs, game accounts, domain names
- **Core engine:** dependency-free Python (stdlib only) - runs anywhere
- **License-ready:** clean, BOM-free, open-source structure

---

## Table of Contents

1. [Why this skill](#why-this-skill)
2. [Key features](#key-features)
3. [How it works](#how-it-works)
4. [Project structure](#project-structure)
5. [Quick start](#quick-start)
6. [The valuation engine (vav)](#the-valuation-engine-vav)
7. [Quality gates](#quality-gates)
8. [Knowledge brain pipeline](#knowledge-brain-pipeline)
9. [Testing](#testing)
10. [Cluster sharing (Phase 5)](#cluster-sharing-phase-5)
11. [Configuration](#configuration)
12. [Graceful degradation](#graceful-degradation)
13. [Roadmap](#roadmap)
14. [Contributing](#contributing)
15. [License](#license)

---

## Why this skill

Owners and buyers of NFTs, game accounts, and domain names have no defensible
way to price illiquid, idiosyncratic digital assets. Naive price-history
averages ignore rarity, liquidity, custody risk, and wash-trading. This skill
triangulates value across multiple named frameworks, discounts risk, refreshes
marketplace data, and emits an artifact - not a chat reply.

### Use cases

1. **Domain appraisal** - triangulate comparable sales, length, keyword value,
   and parking income into a range.
2. **NFT rarity** - compute statistical (trait-frequency) rarity and compare to
   the collection floor.
3. **Game account sale** - value from comparable account sales and progression
   utility (cost/market/income).
4. **Wash-trading audit** - detect round-trip patterns and discount manipulated
   comparables.
5. **Market shift re-pricing** - refresh floor/liquidity and re-price the asset.
6. **Best time to sell** - roadmap of listing strategy and timing ranked by
   effort x impact.

---

## Key features

- **Framework-grounded scoring only** - never ad-hoc rubrics. Six named governing
  frameworks are enforced in code.
- **Deterministic quality gates** - evidence, framework, and challenge gates run
  before any deliverable is emitted; failure refuses or degrades gracefully.
- **Triangulation by design** - requires at least two distinct named frameworks
  per valuation.
- **Wash-trade detection** - on-chain heuristics flag round-trips, price spikes,
  and bot cadence; flagged comparables are excluded.
- **Risk discounting** - platform, custody, wash-trade, and regulatory vectors
  fold into a multiplicative composite haircut.
- **Liquidity-aware** - illiquidity haircuts (up to 35%) and bid-ask depth
  scoring built into the value band.
- **Self-improving knowledge brain** - ArXiv + crawl4ai pipeline, idempotent
  dedupe, weekly cron, graceful offline.
- **Cluster-shared schema** - canonical report schema and gates reused by
  sibling finance-insurance skills (no duplicated logic).
- **Zero hard dependencies** - pure Python stdlib; trivial CI and portable.

---

## How it works

```
User request
   |
   v
sub-profile-intake          -> AssetProfile        (typed)
   |
   v
sub-risk-screener           -> RiskScreen          (+ composite_discount)
   |
   v
knowledge refresh           -> SECOND-KNOWLEDGE-BRAIN.md (if stale > 7d)
   |
   v
sub-market-data-updater     -> MarketDataSnapshot[] (+ composite)
   |
   v
sub-scoring-engine          -> ScoredDimension[]   (>= 2 named frameworks)
   |
   v
quality gates               -> evidence | framework | challenge
   |   (fail + out-of-scope => refuse; fail + in-scope => degrade)
   v
sub-improvement-roadmap     -> RoadmapItem[]       (effort x impact ranked)
   |
   v
SYNTHESIZE                  -> ValuationReport     (6-section artifact)
```

### Governing frameworks (named, never ad-hoc)

1. `comparable_sales_with_liquidity_adjustment` - Comparable-sales (market)
   approach with liquidity adjustment.
2. `income_approach` - Income approach (DCF with Gordon terminal) for
   cash-flowing digital assets.
3. `rarity_scoring_trait_frequency` - Statistical rarity (product-of-rarities,
   geometric-mean normalisation) for NFTs.
4. `liquidity_floor_price_bid_ask_depth` - Floor anchoring and bid-ask depth
   scoring.
5. `intangible_asset_valuation_cost_market_income` - Intangible-asset valuation
   principles (cost/market/income triangulation; IVS 104 / RICS Red Book).
6. `risk_discounting_platform_custody_regulatory` - Risk discounting over
   platform, custody, wash-trade, and regulatory vectors.

---

## Project structure

```
virtual-asset-valuation/
|-- CLAUDE.md                          # skill overview + harness flow
|-- PROJECT-detail.md                  # full technical spec
|-- PROJECT-DEVELOPMENT-PHASE-TRACKING.md   # phase roadmap (0-5 done)
|-- SECOND-KNOWLEDGE-BRAIN.md          # self-improving knowledge base
|-- README.md                          # this file
|-- .gitignore
|
|-- skills/
|   |-- main.md                        # harness entry point
|   |-- sub-profile-intake.md
|   |-- sub-risk-screener.md
|   |-- sub-scoring-engine.md
|   |-- sub-market-data-updater.md
|   |-- sub-improvement-roadmap.md
|   |-- CLUSTER-SHARED.md              # Phase 5 cross-skill wiring
|   `-- schemas/
|       |-- valuation_schema.json      # canonical ValuationReport schema
|       `-- gate_schema.json           # machine-readable gate contract
|
|-- tools/
|   |-- knowledge_updater.py           # ArXiv + crawl4ai brain pipeline
|   `-- vav/                           # core engine (stdlib-only)
|       |-- __init__.py
|       |-- schemas.py                 # typed dataclasses + validators
|       |-- gates.py                   # evidence/framework/challenge gates
|       |-- scoring.py                 # comparables/income/rarity/liquidity
|       |-- risk.py                    # wash-trade + risk vectors + discount
|       |-- marketdata.py             # snapshots + aggregate reducer
|       |-- knowledge.py              # brain read/dedupe/append helpers
|       `-- harness.py                # orchestration + offline dry-run
|
`-- tests/
    |-- conftest.py
    |-- requirements.txt               # pytest>=7.0
    |-- test-scenarios.md              # 6 scenario spec
    |-- test_schemas.py
    |-- test_gates.py
    |-- test_scoring.py
    |-- test_risk.py
    |-- test_harness.py
    `-- fixtures/
        |-- scenario_1_domain.json
        |-- scenario_2_nft_rarity.json
        |-- scenario_3_game_account.json
        |-- scenario_4_wash_trading.json
        |-- scenario_5_market_shift.json
        `-- scenario_6_sell_timing.json
```

---

## Quick start

Requirements: Python 3.9 or newer (no third-party packages needed for the core).

### 1. Run the test suite

```powershell
cd D:\skills\virtual-asset-valuation
python -m pip install -r tests\requirements.txt   # only pytest is required
python -m pytest tests -q
```

Expected: `42 passed`.

### 2. Validate a fixture offline (no LLM, no network)

```python
from vav.schemas import load_fixture
from vav.harness import run_dry

report = load_fixture("tests/fixtures/scenario_1_domain.json")
ok, result = run_dry(report)
print(ok, result.scope_message, result.report.value_low, result.report.value_high)
```

### 3. Run the knowledge brain updater (offline safe)

```powershell
# Dry-run, no network: shows what would be collected
python tools\knowledge_updater.py --dry-run --no-arxiv --no-crawl

# Real run (network required); idempotent - safe to re-run
python tools\knowledge_updater.py --since 2025-01-01 --max 15
```

### 4. Use the skill in a Claude harness

The skill markdown files under `skills/` are the prompt-side contract. The
deterministic core (`tools/vav`) is the machine-side contract. The harness in
`skills/main.md` orchestrates the sub-skills and enforces the gates via
`vav.gates.run_all_gates` and `vav.harness.run_dry` before delivering.

---

## The valuation engine (vav)

`tools/vav` is the dependency-free core. It is the single source of truth shared
by the skill markdown harness and the test suite.

### schemas.py

Typed dataclasses with `validate()` enforcing the quality-gate contract:

- `AssetProfile`, `RiskScreen`, `ScoredDimension`, `RoadmapItem`, `Evidence`
- `ValuationReport` - the synthesised deliverable
- `EvidenceTier` - normative evidence hierarchy
- `Outcome` - `proceed` / `refuse` / `degrade`
- `load_fixture`, `to_json`, `from_json` - serialisation helpers

### scoring.py

Pure, deterministic, framework-grounded math:

| Function | Framework | Returns |
|----------|-----------|---------|
| `comparable_value(sales, weights)` | comparable-sales | (point, low, high) |
| `income_value(cfs, rate, g)` | income (DCF) | (point, low, high) |
| `rarity_score(trait_counts, subject, n)` | rarity | score in [0,1] |
| `liquidity_adjustment(value, liq)` | liquidity haircut | adjusted value |
| `bid_ask_depth_score(bid, ask, spread_bps)` | liquidity/depth | score in [0,1] |
| `triangulate_value(estimates, discount)` | triangulation | (point, low, high) |
| `confidence_band(confs, evidence_n, online)` | confidence | score in [0,1] |

### risk.py

| Function | Purpose |
|----------|---------|
| `wash_trade_flag(transfers)` | heuristics: round-trips, price spikes, bot cadence |
| `custody_risk(model, multi_sig, insured)` | custody risk in [0,1] |
| `platform_risk(marketplace, age, escrow)` | platform risk in [0,1] |
| `regulatory_risk(jurisdiction, asset_class, sanctioned)` | regulatory risk in [0,1] |
| `risk_discount(p, c, w, r, in_scope)` | multiplicative composite discount |

### marketdata.py

`MarketDataSnapshot` + `LiquidityMetrics` plus `aggregate(snapshots)` which fuses
multiple venues via medians (robust to wash-trade outliers).

### knowledge.py

`Brain`, `entry_hash`, `read_brain_hashes`, `append_entries`,
`brain_staleness_days` - pure helpers over `SECOND-KNOWLEDGE-BRAIN.md` for
idempotent, deduplicated, date-stamped appends.

### harness.py

`Harness`, `HarnessStep`, `STEP_ORDER`, and `run_dry(report)` - codifies the
orchestration order from `skills/main.md` and the offline pre-delivery
validation used by tests and any production caller.

---

## Quality gates

Three gates run before any deliverable is shown. They are the single contract
shared by the harness and the tests (machine-readable in
`skills/schemas/gate_schema.json`, implemented in `tools/vav/gates.py`).

| Gate | Rule | On fail |
|------|------|---------|
| Evidence | every material claim traceable to a cited source at tier >= field_study; >= 1 evidence per dimension | block |
| Framework | all scoring cites a named governing framework; >= 2 distinct frameworks (triangulation) | block |
| Challenge | >= 2 substantive devil's-advocate challenges present | block |

Scope rule:
- Out-of-scope or unsafe -> `outcome=refuse`, no value band emitted.
- In-scope but gates fail -> `outcome=degrade`, deliverable emitted with stated
  limitations and reduced confidence.

Evidence tiers (highest first):
`primary_market_data` > `systematic_review` > `meta_analysis` > `rct` >
`benchmark` > `cohort` > `field_study` > `expert_opinion` > `blog`.

---

## Knowledge brain pipeline

`tools/knowledge_updater.py` keeps `SECOND-KNOWLEDGE-BRAIN.md` current.

- **Sources:** ArXiv (`q-fin.PR`, `econ.GN`), optional crawl4ai domain pages
  (namebio.com, opensea.io, blur.io).
- **Scoring:** recency decay (2-year) + domain-keyword relevance.
- **Dedup:** SHA-1 hash of URL/DOI; re-running with the same data adds nothing.
- **Append:** date-stamped rows + Knowledge Update Log line.
- **CLI flags:** `--since`, `--max`, `--dry-run`, `--brain`, `--no-arxiv`,
  `--no-crawl`, `-v`.

Recommended schedule: weekly cron. The brain is currently seeded with real
authoritative valuation standards (IVS 104, RICS Red Book, USPAP, AICPA SSVS).

---

## Testing

```
python -m pytest tests -q
```

42 tests across 6 modules cover schemas, gates, scoring, risk, marketdata
aggregation, harness orchestration, and all 6 scenario fixtures. The fixtures
are the canonical regression set: each is a schema-valid `ValuationReport` that
passes all three gates and the scope rule via `vav.harness.run_dry`.

| Fixture | Scenario | Frameworks used |
|---------|----------|-----------------|
| scenario_1_domain.json | Domain appraisal | comparable-sales, income |
| scenario_2_nft_rarity.json | NFT rarity | rarity, liquidity-floor |
| scenario_3_game_account.json | Game account sale | comparable-sales, cost/market/income |
| scenario_4_wash_trading.json | Wash-trade discount | comparable-sales (discounted), rarity |
| scenario_5_market_shift.json | Market re-pricing | rarity, liquidity-floor |
| scenario_6_sell_timing.json | Best time to sell | liquidity-timing, comparable-sales |

---

## Cluster sharing (Phase 5)

`skills/CLUSTER-SHARED.md` standardises cross-skill wiring for the
finance-insurance cluster so no sibling re-implements scoring logic.

- Siblings import `vav.scoring` / `vav.risk` / `vav.gates` rather than
  re-deriving formulas.
- All siblings emit the canonical `ValuationReport`
  (`skills/schemas/valuation_schema.json`).
- A sibling may only **tighten** gate thresholds (e.g. insurance requiring
  `min_material_tier=rct`), never loosen them.
- Additive schema changes only; existing fixtures and `run_dry` must not break.

---

## Configuration

### Knowledge updater in-file config (`tools/knowledge_updater.py`)

```python
ARXIV_CATEGORIES = ["q-fin.PR", "econ.GN"]
SEARCH_QUERIES = [
    "NFT valuation rarity liquidity",
    "domain name appraisal model",
    "intangible digital asset pricing",
    "virtual goods secondary market",
]
DOMAINS = ["namebio.com", "opensea.io", "blur.io"]
```

### Brain staleness threshold

The harness refreshes the brain when `vav.knowledge.brain_staleness_days() > 7`.
Tune via `Brain.is_stale(threshold_days=7)`.

---

## Graceful degradation

- **Offline** (WebSearch/WebFetch unavailable): the harness still produces a
  deliverable using cached market data and internal knowledge; it sets
  `outcome=degrade`, appends a knowledge-currency limitation, and lowers
  confidence via `confidence_band(..., online=False)`.
- **Out of scope or unsafe**: `outcome=refuse` with a one-line reason; no value
  band is emitted.
- **Updater offline**: `knowledge_updater.py` logs and no-ops; the brain is left
  unchanged (never corrupted).

---

## Roadmap

All build phases (0-5) are complete. Deferred to the production stage only:

- First live `knowledge_updater.py` crawl batch (network run).
- Real marketplace API adapters (OpenSea/Blur/NameBio/PlayerAuctions HTTP
  clients) wired into the `MarketDataSnapshot` contract.

The adapter contract (`vav.marketdata.MarketDataSnapshot`) is already defined, so
adding a live adapter is a drop-in implementation with no schema changes.

---

## Contributing

1. Fork the repo and create a feature branch.
2. Keep the core dependency-free (stdlib only). Any new dependency must be
   optional and gated with a graceful import fallback.
3. Add or update fixtures under `tests/fixtures/` and ensure
   `python -m pytest tests -q` is green.
4. Never loosen gate thresholds; tighten only, and document the change.
5. Schema changes must be additive and must not break `vav.harness.run_dry`.
6. Commit with clear messages and open a pull request against `main`.

---

## License

Released for open-source use. See the repository license file for terms. The
underlying valuation frameworks (IVS 104, RICS Red Book, USPAP, AICPA SSVS) are
standards owned by their respective issuers and are referenced, not reproduced.
