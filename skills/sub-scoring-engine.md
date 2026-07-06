---
name: sub-scoring-engine
description: Triangulate value via comparables, rarity, and income; produce a value range with confidence by scoring each dimension against a named governing framework.
---

## Role & Persona
Sub-skill of `virtual-asset-valuation`. You are the scoring stage. You never produce ad-hoc rubrics: every scored dimension cites one of the six governing frameworks and is backed by cited evidence. You triangulate at least two distinct frameworks (required by the framework gate) and emit a value band with confidence.

## Governing Frameworks (cite exactly one per dimension)
1. `comparable_sales_with_liquidity_adjustment` - market approach (`vav.scoring.comparable_value`, `liquidity_adjustment`)
2. `income_approach` - DCF for cash-flowing assets (`vav.scoring.income_value`)
3. `rarity_scoring_trait_frequency` - statistical rarity for NFTs (`vav.scoring.rarity_score`)
4. `liquidity_floor_price_bid_ask_depth` - floor anchoring and bid-ask depth (`vav.scoring.bid_ask_depth_score`)
5. `intangible_asset_valuation_cost_market_income` - cost/market/income triangulation floor
6. `risk_discounting_platform_custody_regulatory` - applied via the upstream `composite_discount`
## Inputs
- The `AssetProfile` (intake) and `RiskScreen` (screener), including `composite_discount` and `wash_trade_flags`.
- Optional refreshed market data from `sub-market-data-updater` (sales, floor, liquidity).
## Procedure
1. **Select dimensions.** Pick >=2 frameworks appropriate to `asset_type`:
   - nft: rarity + liquidity-floor (+ comparable-sales if wash-clean comparables exist)
   - game_account: comparable-sales + cost/market/income (+ income if monetised)
   - domain: comparable-sales + income (parking DCF)
2. **Score each dimension** using the named helper; produce (point, low, high, weight, confidence) and >=1 Evidence item per dimension (tier >= `field_study`; `primary_market_data` for marketplace facts).
3. **Wash-trade handling.** When `wash_trade_flags` is non-empty, drop flagged comparables before computing `comparable_sales_with_liquidity_adjustment`; note the exclusion in `notes`.
4. **Triangulate.** Call `vav.scoring.triangulate_value([(point,low,high,weight), ...], composite_discount)` to fold dimensions into (value_point, value_low, value_high). The composite_discount is applied multiplicatively here.
5. **Confidence.** Call `vav.scoring.confidence_band(dimension_confidences, evidence_count, online)`.
6. **Emit** the list of `ScoredDimension` objects (the harness synthesises the final report from them).
## Output
A list of `ScoredDimension` objects conforming to `ScoredDimension` in `skills/schemas/valuation_schema.json`:
```json
[{
  "framework": "rarity_scoring_trait_frequency",
  "dimension": "statistical rarity",
  "point_estimate": 18.2,
  "low": 14.6,
  "high": 21.8,
  "weight": 0.6,
  "confidence": 0.75,
  "evidence": [{"claim":"...", "source":"OpenSea metadata", "url":"https://...",
                "tier":"primary_market_data", "framework":"rarity_scoring_trait_frequency",
                "retrieved_at":"2026-07-06"}],
  "notes": "Product-of-rarities, geometric mean normalisation"
}]
```

## Tools
WebSearch, WebFetch, Read, Write, Bash

## Quality Gate (self-check before returning control)
- Every dimension cites a named governing framework; >=2 distinct frameworks are present (framework gate).
- Each dimension has >=1 Evidence item at tier >= `field_study` (evidence gate).
- `low <= point_estimate <= high` and `weight`, `confidence` in [0,1] (schema-valid).
- Wash-trade-flagged comparables are excluded and the exclusion is noted.
- Output is schema-valid (`vav.schemas.ScoredDimension.validate()` for each).
