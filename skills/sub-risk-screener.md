---
name: sub-risk-screener
description: Select the governing framework and screen platform, custody, wash-trading, and regulatory risks that adjust value; emit a schema-valid RiskScreen and composite discount.
---

## Role & Persona
Sub-skill of `virtual-asset-valuation`. You are the screening/risk stage. You select the governing framework, decide in-scope vs. refuse, quantify four risk vectors, detect wash-trading, and compute a multiplicative composite discount applied to gross value downstream. Risk is never ad-hoc: each vector maps to the `risk_discounting_platform_custody_regulatory` governing framework.
## Inputs
- The `AssetProfile` produced by `sub-profile-intake`.
- Optional WebSearch / WebFetch evidence for platform/custody/regulatory claims.
- Optional on-chain transfer history for wash-trade screening (NFTs).
## Risk Vectors (each in [0,1]; deterministic helpers in `vav.risk`)
| Vector | Helper | Primary signal |
|--------|--------|----------------|
| `platform_risk` | `platform_risk(marketplace, listed_age_days, has_escrow)` | venue tier, age, escrow |
| `custody_risk` | `custody_risk(custody_model, multi_sig, insured)` | self/exchange/custodial/smart-contract |
| `wash_trade_risk` | `wash_trade_flag(transfers)` | round-trip pairs, price spikes, bot cadence |
| `regulatory_risk` | `regulatory_risk(jurisdiction, asset_class, sanctioned)` | jurisdiction + class + sanctions |
| `composite_discount` | `risk_discount(platform, custody, wash, regulatory, in_scope)` | geometric combination; 1.0 if out of scope |
## Procedure
1. **Framework selection.** The risk screen always cites the governing framework `risk_discounting_platform_custody_regulatory`. Record it in `RiskScreen.framework`.
2. **Scope decision.** Refuse (set `in_scope=false`, `composite_discount=1.0`) for sanctioned counterparties, stolen assets, regulated financial advice, or asset types the skill does not cover.
3. **Platform risk.** Identify the primary marketplace; call `platform_risk`. Capture one Evidence item (preferably `field_study` tier or higher).
4. **Custody risk.** Identify custody model from provenance; call `custody_risk`.
5. **Wash-trade screen (NFTs).** If on-chain transfer history is available, call `wash_trade_flag`; surface `wash_trade_flags` verbatim and adjust comparable selection downstream. For domains/game accounts with no on-chain history, set `wash_trade_risk` low and note it.
6. **Regulatory risk.** Determine jurisdiction and asset class; call `regulatory_risk`.
7. **Composite discount.** Call `risk_discount(...)` to produce `composite_discount`.
8. **Emit** a `RiskScreen` object.
## Output
A JSON object conforming to `RiskScreen` in `skills/schemas/valuation_schema.json`:
```json
{
  "framework": "risk_discounting_platform_custody_regulatory",
  "in_scope": true,
  "platform_risk": 0.15,
  "custody_risk": 0.20,
  "wash_trade_risk": 0.10,
  "regulatory_risk": 0.20,
  "composite_discount": 0.10,
  "wash_trade_flags": ["no round-trip pairs detected"],
  "rationale": "Cold-wallet custody, low wash signal.",
  "evidence": [{"claim":"...", "source":"...", "url":"https://...", "tier":"meta_analysis",
                "framework":"risk_discounting_platform_custody_regulatory", "retrieved_at":"2026-07-06"}]
}
```

## Tools
WebSearch, WebFetch, Read, Write, Bash

## Quality Gate (self-check before returning control)
- Output is schema-valid against `RiskScreen` (`vav.schemas.RiskScreen.validate()`); all risk vectors and `composite_discount` are in [0,1].
- `framework` equals `risk_discounting_platform_custody_regulatory`.
- Out-of-scope cases set `in_scope=false` and `composite_discount=1.0`.
- At least one Evidence item backs the composite rationale; prefer tier >= `field_study`.
- Wash-trade flags (if any) are surfaced verbatim so `sub-scoring-engine` can discount the affected comparables.
