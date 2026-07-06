"""vav - Virtual Asset Valuation core library.

Production-grade, dependency-free core for the `virtual-asset-valuation` skill.
Provides typed schemas, quality gates, deterministic scoring math, risk
screening, market-data adapter contracts, knowledge-brain helpers, and a
harness orchestration contract used by both the skill markdown harness and the
pytest regression suite.

Modules are intentionally framework-grounded (comparable-sales / market approach
with liquidity adjustment, income approach, rarity scoring, liquidity & floor
analysis, intangible-asset valuation principles, risk discounting) so that
every scoring dimension cites a named framework.
"""
from .schemas import (
    AssetProfile,
    RiskScreen,
    ScoredDimension,
    ValuationReport,
    RoadmapItem,
    Evidence,
    EvidenceTier,
    AssetType,
    ValuationPurpose,
    Outcome,
    ValidationError,
    load_fixture,
    to_json,
    from_json,
)
from .gates import (
    evidence_gate,
    framework_gate,
    challenge_gate,
    run_all_gates,
    GateResult,
    ScopeDecision,
    refuse_out_of_scope,
)
from .scoring import (
    comparable_value,
    income_value,
    rarity_score,
    liquidity_adjustment,
    bid_ask_depth_score,
    triangulate_value,
    confidence_band,
)
from .risk import (
    wash_trade_flag,
    risk_discount,
    custody_risk,
    platform_risk,
    regulatory_risk,
)
from .marketdata import MarketDataSnapshot, LiquidityMetrics, aggregate
from .knowledge import (
    Brain,
    entry_hash,
    read_brain_hashes,
    append_entries,
    brain_staleness_days,
)
from .harness import Harness, HarnessStep, run_dry

__all__ = [
    "AssetProfile",
    "RiskScreen",
    "ScoredDimension",
    "ValuationReport",
    "RoadmapItem",
    "Evidence",
    "EvidenceTier",
    "AssetType",
    "ValuationPurpose",
    "Outcome",
    "ValidationError",
    "load_fixture",
    "to_json",
    "from_json",
    "evidence_gate",
    "framework_gate",
    "challenge_gate",
    "run_all_gates",
    "GateResult",
    "ScopeDecision",
    "refuse_out_of_scope",
    "comparable_value",
    "income_value",
    "rarity_score",
    "liquidity_adjustment",
    "bid_ask_depth_score",
    "triangulate_value",
    "confidence_band",
    "wash_trade_flag",
    "risk_discount",
    "custody_risk",
    "platform_risk",
    "regulatory_risk",
    "MarketDataSnapshot",
    "LiquidityMetrics",
    "aggregate",
    "Brain",
    "entry_hash",
    "read_brain_hashes",
    "append_entries",
    "brain_staleness_days",
    "Harness",
    "HarnessStep",
    "run_dry",
]
__version__ = "1.0.0"
