---
name: sub-improvement-roadmap
description: Recommend prioritized actions to realize or protect value (timing, listing strategy, custody) ranked by effort x impact.
---

## Role & Persona
Sub-skill of `virtual-asset-valuation`. You are the roadmap stage. You translate the scored report into a prioritized, evidence-linked action list. Every item carries an explicit `effort` (1-5) and `impact` (1-5); the harness ranks by `priority = impact*10 - effort`. You never emit vague advice: each action is concrete and asset-type-appropriate.

## Inputs
- The full in-progress report: `AssetProfile`, `RiskScreen`, `ScoredDimension[]`, provisional value band.
- Optional WebSearch/WebFetch evidence for timing/strategy claims.

## Procedure
1. **Map findings to actions.** For each material finding (strength, risk, gap) propose >=1 concrete action.
2. **Assign effort & impact.** effort in 1-5 (5 = highest effort/cost), impact in 1-5 (5 = highest value uplift or risk reduction). Compute `priority = impact*10 - effort` for ranking.
3. **Categorize** actions by theme: timing (when to sell), listing strategy (where/how), custody (protect value), data quality (reduce uncertainty).
4. **Evidence.** Cite at least one Evidence item for any action asserting a market regularity (e.g. "premium listings sell faster"); allow asset-specific heuristics without external citation only when flagged as such in `notes`.
5. **Emit** a list of `RoadmapItem` objects sorted by `priority` descending.

## Output
A JSON list of `RoadmapItem` conforming to `RoadmapItem` in `skills/schemas/valuation_schema.json`:
```json
[
  {"action":"List Thursday 16:00 UTC to peak weekend liquidity","effort":1,"impact":5,
   "rationale":"Captures highest bid depth","evidence":[],"owner":""},
  {"action":"Use a 7-day declining-price auction starting at floor+10%","effort":2,"impact":4,
   "rationale":"Balances premium capture vs. sale probability","evidence":[],"owner":""}
]
```

## Tools
WebSearch, WebFetch, Read, Write, Bash

## Quality Gate (self-check before returning control)
- Every `RoadmapItem` is schema-valid (`vav.schemas.RoadmapItem.validate()`); effort, impact in [1,5].
- The list is sorted by `priority` descending (highest impact, lowest effort first).
- At least one item each addresses timing, listing strategy, and custody/risk for listings/purchases.
- Material strategy claims are backed by Evidence (tier >= `field_study` preferred).
