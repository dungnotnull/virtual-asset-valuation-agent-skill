"""Typed schemas and validators for the virtual-asset-valuation skill.

Implemented with stdlib dataclasses + enums so the package has zero hard runtime
dependencies and can run on any Python 3.9+ environment (incl. CI sandboxes).
Every dataclass carries a `validate()` that enforces the quality-gate contract
declared in the skill markdown files.
"""
from __future__ import annotations

import json
import os
from dataclasses import asdict, dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional


class ValidationError(ValueError):
    """Raised when a schema object fails its quality-gate validation."""


class AssetType(str, Enum):
    NFT = "nft"
    GAME_ACCOUNT = "game_account"
    DOMAIN = "domain"


class ValuationPurpose(str, Enum):
    APPRAISAL = "appraisal"
    LISTING = "listing"
    PURCHASE = "purchase"
    PORTFOLIO = "portfolio"
    COLLATERAL = "collateral"


class EvidenceTier(str, Enum):
    """Evidence hierarchy used by the evidence gate (higher index = stronger)."""
    BLOG = "blog"
    EXPERT_OPINION = "expert_opinion"
    FIELD_STUDY = "field_study"
    COHORT = "cohort"
    BENCHMARK = "benchmark"
    RCT = "rct"
    META_ANALYSIS = "meta_analysis"
    SYSTEMATIC_REVIEW = "systematic_review"
    PRIMARY_MARKET_DATA = "primary_market_data"

    @classmethod
    def rank(cls, tier: "EvidenceTier") -> int:
        order = [
            cls.BLOG, cls.EXPERT_OPINION, cls.FIELD_STUDY, cls.COHORT,
            cls.BENCHMARK, cls.RCT, cls.META_ANALYSIS, cls.SYSTEMATIC_REVIEW,
            cls.PRIMARY_MARKET_DATA,
        ]
        return order.index(tier)


class Outcome(str, Enum):
    PROCEED = "proceed"
    REFUSE = "refuse"
    DEGRADE = "degrade"


# Named governing frameworks. Every scored dimension MUST cite one of these.
GOVERNING_FRAMEWORKS = (
    "comparable_sales_with_liquidity_adjustment",
    "income_approach",
    "rarity_scoring_trait_frequency",
    "liquidity_floor_price_bid_ask_depth",
    "intangible_asset_valuation_cost_market_income",
    "risk_discounting_platform_custody_regulatory",
)

VALID_FRAMEWORKS = set(GOVERNING_FRAMEWORKS)


@dataclass
class Evidence:
    """A single cited source backing a material claim."""
    claim: str
    source: str
    url: str
    tier: EvidenceTier
    framework: Optional[str] = None
    retrieved_at: str = ""  # ISO-8601 date

    def validate(self) -> None:
        if not self.claim.strip():
            raise ValidationError("evidence.claim must not be empty")
        if not self.source.strip():
            raise ValidationError("evidence.source must not be empty")
        if not self.url.strip():
            raise ValidationError("evidence.url must not be empty")
        if not isinstance(self.tier, EvidenceTier):
            raise ValidationError("evidence.tier must be an EvidenceTier")
        if self.framework is not None and self.framework not in VALID_FRAMEWORKS:
            raise ValidationError(
                "evidence.framework '%s' is not a named governing framework" % self.framework
            )


@dataclass
class AssetProfile:
    """Output of sub-profile-intake."""
    asset_type: AssetType
    purpose: ValuationPurpose
    identifiers: Dict[str, str]          # e.g. {"chain":"ethereum","contract":"0x...","token_id":"123"}
    provenance: str
    utility: str
    attributes: Dict[str, Any] = field(default_factory=dict)
    assumptions: List[str] = field(default_factory=list)
    notes: str = ""

    def validate(self) -> None:
        if not isinstance(self.asset_type, AssetType):
            raise ValidationError("asset_type must be an AssetType")
        if not isinstance(self.purpose, ValuationPurpose):
            raise ValidationError("purpose must be a ValuationPurpose")
        if not self.identifiers:
            raise ValidationError("identifiers must not be empty")
        if not self.provenance.strip():
            raise ValidationError("provenance must not be empty")
        if not self.utility.strip():
            raise ValidationError("utility must not be empty")


@dataclass
class RiskScreen:
    """Output of sub-risk-screener."""
    framework: str
    in_scope: bool
    platform_risk: float          # 0..1 (1 = highest risk)
    custody_risk: float
    wash_trade_risk: float
    regulatory_risk: float
    composite_discount: float     # 0..1 multiplicative discount applied to value
    wash_trade_flags: List[str] = field(default_factory=list)
    rationale: str = ""
    evidence: List[Evidence] = field(default_factory=list)

    def validate(self) -> None:
        if self.framework not in VALID_FRAMEWORKS:
            raise ValidationError(
                "risk.framework '%s' is not a named governing framework" % self.framework
            )
        for name, v in (("platform_risk", self.platform_risk),
                        ("custody_risk", self.custody_risk),
                        ("wash_trade_risk", self.wash_trade_risk),
                        ("regulatory_risk", self.regulatory_risk),
                        ("composite_discount", self.composite_discount)):
            if not 0.0 <= v <= 1.0:
                raise ValidationError("%s must be in [0,1], got %r" % (name, v))
        if not self.rationale.strip():
            raise ValidationError("rationale must not be empty")
        for e in self.evidence:
            e.validate()


@dataclass
class ScoredDimension:
    """Output of sub-scoring-engine (one dimension)."""
    framework: str
    dimension: str
    point_estimate: float
    low: float
    high: float
    weight: float               # 0..1
    confidence: float            # 0..1
    evidence: List[Evidence] = field(default_factory=list)
    notes: str = ""

    def validate(self) -> None:
        if self.framework not in VALID_FRAMEWORKS:
            raise ValidationError(
                "dimension.framework '%s' is not a named governing framework" % self.framework
            )
        if not self.dimension.strip():
            raise ValidationError("dimension must not be empty")
        if not (self.low <= self.point_estimate <= self.high):
            raise ValidationError(
                "point_estimate must lie within [low, high]: %r not in [%r, %r]"
                % (self.point_estimate, self.low, self.high)
            )
        if not 0.0 <= self.weight <= 1.0:
            raise ValidationError("weight must be in [0,1]")
        if not 0.0 <= self.confidence <= 1.0:
            raise ValidationError("confidence must be in [0,1]")
        for e in self.evidence:
            e.validate()


@dataclass
class RoadmapItem:
    """Output of sub-improvement-roadmap."""
    action: str
    effort: int                  # 1..5 (5 = highest effort)
    impact: int                  # 1..5 (5 = highest impact)
    rationale: str
    evidence: List[Evidence] = field(default_factory=list)
    owner: str = ""

    def validate(self) -> None:
        if not self.action.strip():
            raise ValidationError("roadmap.action must not be empty")
        if not 1 <= self.effort <= 5:
            raise ValidationError("effort must be in [1,5]")
        if not 1 <= self.impact <= 5:
            raise ValidationError("impact must be in [1,5]")
        if not self.rationale.strip():
            raise ValidationError("rationale must not be empty")
        for e in self.evidence:
            e.validate()

    @property
    def priority(self) -> int:
        """effort x impact ranking (lower effort, higher impact => higher)."""
        return self.impact * 10 - self.effort


@dataclass
class ValuationReport:
    """Final synthesised deliverable emitted by the harness."""
    profile: AssetProfile
    risk: RiskScreen
    dimensions: List[ScoredDimension]
    roadmap: List[RoadmapItem]
    value_point: float
    value_low: float
    value_high: float
    confidence: float
    challenges: List[str]
    limitations: List[str]
    outcome: Outcome

    def validate(self) -> None:
        self.profile.validate()
        self.risk.validate()
        if not self.dimensions:
            raise ValidationError("at least one scored dimension is required")
        for d in self.dimensions:
            d.validate()
        for r in self.roadmap:
            r.validate()
        if not (self.value_low <= self.value_point <= self.value_high):
            raise ValidationError("value_point must lie in [value_low, value_high]")
        if not 0.0 <= self.confidence <= 1.0:
            raise ValidationError("confidence must be in [0,1]")
        if not isinstance(self.outcome, Outcome):
            raise ValidationError("outcome must be an Outcome")
        # Each dimension must cite a distinct framework unless framework allows
        # multiple dimensions; frameworks may repeat but every dimension cites one.
        for c in self.challenges:
            if not c.strip():
                raise ValidationError("challenge strings must not be empty")


# ---------------------------------------------------------------------------
# Serialisation helpers
# ---------------------------------------------------------------------------

def _coerce_enum(obj: Any, enum: type) -> Any:
    if isinstance(obj, enum):
        return obj
    return enum(obj)


def _evidence_from_dict(d: Dict[str, Any]) -> Evidence:
    return Evidence(
        claim=d["claim"],
        source=d["source"],
        url=d["url"],
        tier=EvidenceTier(d["tier"]),
        framework=d.get("framework"),
        retrieved_at=d.get("retrieved_at", ""),
    )


def profile_from_dict(d: Dict[str, Any]) -> AssetProfile:
    return AssetProfile(
        asset_type=_coerce_enum(d["asset_type"], AssetType),
        purpose=_coerce_enum(d["purpose"], ValuationPurpose),
        identifiers=dict(d["identifiers"]),
        provenance=d["provenance"],
        utility=d["utility"],
        attributes=dict(d.get("attributes", {})),
        assumptions=list(d.get("assumptions", [])),
        notes=d.get("notes", ""),
    )


def risk_from_dict(d: Dict[str, Any]) -> RiskScreen:
    return RiskScreen(
        framework=d["framework"],
        in_scope=bool(d["in_scope"]),
        platform_risk=float(d["platform_risk"]),
        custody_risk=float(d["custody_risk"]),
        wash_trade_risk=float(d["wash_trade_risk"]),
        regulatory_risk=float(d["regulatory_risk"]),
        composite_discount=float(d["composite_discount"]),
        wash_trade_flags=list(d.get("wash_trade_flags", [])),
        rationale=d["rationale"],
        evidence=[_evidence_from_dict(e) for e in d.get("evidence", [])],
    )


def dimension_from_dict(d: Dict[str, Any]) -> ScoredDimension:
    return ScoredDimension(
        framework=d["framework"],
        dimension=d["dimension"],
        point_estimate=float(d["point_estimate"]),
        low=float(d["low"]),
        high=float(d["high"]),
        weight=float(d["weight"]),
        confidence=float(d["confidence"]),
        evidence=[_evidence_from_dict(e) for e in d.get("evidence", [])],
        notes=d.get("notes", ""),
    )


def roadmap_from_dict(d: Dict[str, Any]) -> RoadmapItem:
    return RoadmapItem(
        action=d["action"],
        effort=int(d["effort"]),
        impact=int(d["impact"]),
        rationale=d["rationale"],
        evidence=[_evidence_from_dict(e) for e in d.get("evidence", [])],
        owner=d.get("owner", ""),
    )


def report_from_dict(d: Dict[str, Any]) -> ValuationReport:
    return ValuationReport(
        profile=profile_from_dict(d["profile"]),
        risk=risk_from_dict(d["risk"]),
        dimensions=[dimension_from_dict(x) for x in d["dimensions"]],
        roadmap=[roadmap_from_dict(x) for x in d["roadmap"]],
        value_point=float(d["value_point"]),
        value_low=float(d["value_low"]),
        value_high=float(d["value_high"]),
        confidence=float(d["confidence"]),
        challenges=list(d.get("challenges", [])),
        limitations=list(d.get("limitations", [])),
        outcome=_coerce_enum(d["outcome"], Outcome),
    )


def to_json(obj: Any) -> str:
    def _default(o: Any) -> Any:
        if isinstance(o, Enum):
            return o.value
        if hasattr(o, "validate"):
            o.validate()
        return asdict(o)
    return json.dumps(obj, default=_default, indent=2, ensure_ascii=False, sort_keys=True)


def from_json(payload: str) -> ValuationReport:
    return report_from_dict(json.loads(payload))


def load_fixture(path: str) -> ValuationReport:
    with open(path, encoding="utf-8") as fh:
        return report_from_dict(json.load(fh))


def repo_root() -> str:
    return os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
