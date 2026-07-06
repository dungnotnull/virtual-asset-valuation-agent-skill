# tests/test-scenarios.md - Virtual Asset / Digital Item Valuation (NFT / game / domain)

Scenario-based tests for the `virtual-asset-valuation` harness. Each scenario has
a machine fixture in `tests/fixtures/` and is validated by `vav.harness.run_dry`
and `vav.gates.run_all_gates` in `tests/test_harness.py` and `tests/test_gates.py`.
Run all with `python -m pytest tests -q`.

### Scenario 1 - Domain appraisal
- **Given:** User wants a domain appraised; skill triangulates comparables, length, and keyword value into a range.
- **Fixture:** `tests/fixtures/scenario_1_domain.json`
- **Expected:** intake confirms inputs -> framework selected -> `sub-scoring-engine` scores comparable-sales + income -> gates pass -> scored report + prioritized roadmap with citations.
- **Pass criteria:** all gates pass; every score cites its framework; roadmap items are effort/impact-ranked.

### Scenario 2 - NFT rarity
- **Given:** An NFT's rarity is unclear; skill computes statistical rarity and compares to collection floor.
- **Fixture:** `tests/fixtures/scenario_2_nft_rarity.json`
- **Expected:** rarity + liquidity-floor frameworks; value band with confidence.
- **Pass criteria:** gates pass; frameworks cited.

### Scenario 3 - Game account sale
- **Given:** A game account is for sale; skill values it from comparable account sales and progression utility.
- **Fixture:** `tests/fixtures/scenario_3_game_account.json`
- **Expected:** comparable-sales + cost/market/income frameworks.
- **Pass criteria:** gates pass; roadmap items are effort/impact-ranked.

### Scenario 4 - Wash-trading discount
- **Given:** Wash-trading inflates an NFT's history; risk screener discounts manipulated comparables.
- **Fixture:** `tests/fixtures/scenario_4_wash_trading.json`
- **Expected:** `wash_trade_flag` flags round-trips; comparables discounted; composite discount applied.
- **Pass criteria:** gates pass; wash-trade flags surfaced; value reflects discount.

### Scenario 5 - Market shift re-pricing
- **Given:** Market data shifts; updater refreshes floor/liquidity and re-prices the asset.
- **Fixture:** `tests/fixtures/scenario_5_market_shift.json`
- **Expected:** refreshed floor + degraded liquidity -> larger illiquidity haircut.
- **Pass criteria:** gates pass; re-anchored value band.

### Scenario 6 - Best time to sell
- **Given:** Owner asks the best time to sell; roadmap recommends listing strategy and timing.
- **Fixture:** `tests/fixtures/scenario_6_sell_timing.json`
- **Expected:** liquidity-timing + comparable frameworks; prioritized roadmap (timing/listing/custody).
- **Pass criteria:** gates pass; roadmap items sorted by priority desc.

## Cross-cutting checks (validated in tests/)
- **Graceful degradation:** with WebSearch/WebFetch disabled, the harness still produces a deliverable (`confidence_band(..., online=False)`) and states the knowledge-currency limitation.
- **Refusal/scope:** out-of-scope or unsafe requests return `outcome=refuse` (`test_harness_refuse_flow`).
- **Determinism of structure:** every run yields the six Output-Format sections (schema-valid `ValuationReport`).
