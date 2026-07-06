# SECOND-KNOWLEDGE-BRAIN.md - Virtual Asset / Digital Item Valuation (NFT / game / domain)

> Self-improving domain knowledge base for the `virtual-asset-valuation` skill.
> Grown continuously by `tools/knowledge_updater.py`. Entries are deduplicated by
> URL/DOI hash and date-stamped.

## Core Concepts and Frameworks
- **Comparable-sales (market) approach with liquidity adjustment** - triangulate recent realised prices, then apply an illiquidity haircut (up to 35%).
- **Income approach** - discounted cash flow (Gordon terminal) for cash-flowing digital assets (parked domains, monetised game accounts).
- **Rarity scoring (trait frequency / statistical rarity)** - product-of-rarities with geometric-mean normalisation for NFTs.
- **Liquidity and floor-price analysis + bid-ask depth** - floor anchoring and order-book depth/spread scoring.
- **Intangible-asset valuation principles** - cost / market / income triangulation (IVS 104, RICS Red Book).
- **Risk discounting** - multiplicative composite haircut over platform, custody, wash-trade, and regulatory vectors.

## Authoritative Standards (seed)
| Standard | Issuer | Scope |
|----------|--------|-------|
| International Valuation Standards (IVS) - IVS 104 Bases of Value | International Valuation Standards Council (IVSC) | Intangible-asset valuation bases |
| RICS Red Book (Global Valuation Standards) | Royal Institution of Chartered Surveyors | Valuation methodology and reporting |
| USPAP (Uniform Standards of Professional Appraisal Practice) | Appraisal Standards Board (TIA) | Appraisal practice (US) |
| AICPA / SSVS - Standards for Valuation of Intangible Assets | AICPA | Intangible-asset valuation (US) |

## Key Research Papers
| Title | Authors | Year | Venue | DOI/Link | Relevance |
|-------|---------|------|-------|----------|-----------|
| _(seed - populate via `tools/knowledge_updater.py`)_ | - | - | - | - | Foundational references for Finance, Investment and Insurance. |

## State-of-the-Art Methods and Tools
- Apply the frameworks above as the scoring backbone.
- Prefer the highest available evidence tier (Systematic Review > Meta-Analysis > RCT/benchmark > Cohort/field study > Expert opinion > Blog); marketplace facts use `primary_market_data`.
- Triangulate multiple sources before asserting a numeric score.
- Detect and discount wash-traded comparables before computing market value.

## Authoritative Data Sources
- NFT marketplace data (OpenSea, Blur, Magic Eden public stats)
- Domain sales comparables (NameBio, Dan.com, GoDaddy auctions)
- Game-asset marketplaces and trade indices (PlayerAuctions, G2G)
- IVS / RICS / USPAP / AICPA intangible-asset valuation standards
- ArXiv categories q-fin.PR, econ.GN and Google Scholar for digital-asset pricing research

## Analytical Frameworks (Scoring Backbone)
The skill scores every deliverable against the named frameworks above; each scoring dimension cites the framework it derives from. The machine contract is `tools/vav/scoring.py` and `skills/schemas/valuation_schema.json`.

## Self-Update Protocol
- **Tool:** `tools/knowledge_updater.py`
- **ArXiv categories:** q-fin.PR, econ.GN
- **Search queries:**
  - `NFT valuation rarity liquidity`
  - `domain name appraisal model`
  - `intangible digital asset pricing`
  - `virtual goods secondary market`
- **Domains:** namebio.com, opensea.io, blur.io
- **Frequency:** weekly cron (graceful no-op when offline).
- **Append format:** date-stamped row in Key Research Papers plus a Knowledge Update Log line; deduplicate by URL/DOI hash.

## Knowledge Update Log
- 2026-06-18 - Brain initialized with core frameworks and seed sources for `virtual-asset-valuation`.
- 2026-07-06 - Brain seeded with authoritative valuation standards (IVS 104, RICS Red Book, USPAP, AICPA SSVS) for Phase 3 completion.
