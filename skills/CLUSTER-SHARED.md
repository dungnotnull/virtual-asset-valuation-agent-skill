# CLUSTER-SHARED.md - Cross-skill wiring for the finance-insurance cluster

> Phase 5 deliverable. This file standardizes the scoring schema and sub-skill
> references shared with sibling skills in the `finance-insurance` cluster
> (e.g. intangible-asset / investment / insurance valuation skills) so no scoring
> logic is duplicated across siblings.

## Shared canonical schema
All cluster siblings emit and accept the canonical report schema:
- `skills/schemas/valuation_schema.json` - `ValuationReport` and sub-objects (`AssetProfile`, `RiskScreen`, `ScoredDimension`, `RoadmapItem`, `Evidence`).
- `skills/schemas/gate_schema.json` - the three quality gates and thresholds.
- Python reference implementation: `tools/vav/` (`schemas.py`, `gates.py`, `scoring.py`, `risk.py`).

## Reusable sub-skills (importable by siblings)
| Sub-skill | File | Reuse rationale |
|-----------|------|-----------------|
| `sub-profile-intake` | `skills/sub-profile-intake.md` | Generic `AssetProfile` intake for any intangible/virtual asset. |
| `sub-risk-screener` | `skills/sub-risk-screener.md` | Generic `risk_discounting_platform_custody_regulatory` screen with composite discount. |
| `sub-scoring-engine` | `skills/sub-scoring-engine.md` | Framework-grounded triangulation (>=2 frameworks); asset-type selects dimensions. |
| `sub-market-data-updater` | `skills/sub-market-data-updater.md` | Venue-agnostic `MarketDataSnapshot` plus `aggregate` reducer. |
| `sub-improvement-roadmap` | `skills/sub-improvement-roadmap.md` | Generic effort x impact roadmap. |

## Standardization rules (to avoid duplicated logic)
1. **No sibling re-implements scoring math.** Cluster siblings import `vav.scoring` and `vav.risk` rather than re-deriving comparable/income/rarity/liquidity formulas.
2. **Single gate contract.** All siblings enforce `vav.gates.run_all_gates` with thresholds from `gate_schema.json`; a sibling may only tighten thresholds (e.g. insurance may require `min_material_tier=rct`), never loosen them.
3. **Shared evidence tiers.** `EvidenceTier` ordering is normative across the cluster.
4. **Naming.** Sibling skills reference sub-skills by their stable `name` slug and the shared schema id; no skill invents a parallel schema.
5. **Backward compatibility.** Additive schema changes only; new optional fields must not break existing fixtures or `vav.harness.run_dry`.

## Integration checklist for a sibling skill
- [ ] Depends on `tools/vav` (or copies the canonical JSON schema) rather than re-defining `ValuationReport`.
- [ ] Reuses >=3 of the shared sub-skills above.
- [ ] Pins the same gate thresholds (or tighter) in its own `gate_schema` extension.
- [ ] Includes regression fixtures validated by `vav.harness.run_dry`.
