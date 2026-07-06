"""Quality gates for the virtual-asset-valuation harness.

The three gates declared in skills/main.md are implemented as deterministic
predicates that operate on a `ValuationReport` (and its sub-stages). They are
the single source of truth shared by the skill markdown harness and the pytest
regression suite, guaranteeing the contract is identical in both worlds.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import List, Tuple

from .schemas import (
    Evidence,
    EvidenceTier,
    GOVERNING_FRAMEWORKS,
    Outcome,
    RiskScreen,
    ScoredDimension,
    ValuationReport,
    VALID_FRAMEWORKS,
)


# Minimum evidence tier required for any material numeric claim.
MIN_MATERIAL_TIER = EvidenceTier.FIELD_STUDY
# Minimum number of evidence items per scored dimension.
MIN_EVIDENCE_PER_DIMENSION = 1
# Minimum confidence required to PROCEED without explicit DEGRADE limitation.
MIN_PROCEED_CONFIDENCE = 0.5
# Minimum number of devil's-advocate challenge statements.
MIN_CHALLENGES = 2


@dataclass
class GateResult:
    name: str
    passed: bool
    reasons: List[str] = field(default_factory=list)

    def __bool__(self) -> bool:
        return self.passed


def evidence_gate(report: ValuationReport) -> GateResult:
    """Every material claim is traceable to a cited source; prefer highest tier."""
    reasons: List[str] = []
    if not report.dimensions:
        return GateResult("evidence", False, ["no scored dimensions present"])

    covered_frameworks = set()
    for dim in report.dimensions:
        if len(dim.evidence) < MIN_EVIDENCE_PER_DIMENSION:
            reasons.append(
                "dimension '%s' has %d evidence items (< %d)"
                % (dim.dimension, len(dim.evidence), MIN_EVIDENCE_PER_DIMENSION)
            )
            continue
        for ev in dim.evidence:
            if not ev.url.strip():
                reasons.append("evidence for '%s' missing url" % dim.dimension)
            if EvidenceTier.rank(ev.tier) < EvidenceTier.rank(MIN_MATERIAL_TIER):
                reasons.append(
                    "evidence for '%s' below minimum tier %s (got %s)"
                    % (dim.dimension, MIN_MATERIAL_TIER.value, ev.tier.value)
                )
            if ev.framework:
                covered_frameworks.add(ev.framework)

    # Composite value range is itself a material claim: must be backed by at
    # least one piece of evidence across the report.
    total_evidence = sum(len(d.evidence) for d in report.dimensions) + len(report.risk.evidence)
    if total_evidence == 0:
        reasons.append("report contains no evidence at all")

    if reasons:
        return GateResult("evidence", False, reasons)
    return GateResult("evidence", True)


def framework_gate(report: ValuationReport) -> GateResult:
    """All scoring is grounded in the named frameworks - never ad-hoc criteria."""
    reasons: List[str] = []
    used = set()
    for dim in report.dimensions:
        if dim.framework not in VALID_FRAMEWORKS:
            reasons.append(
                "dimension '%s' cites unknown framework '%s'" % (dim.dimension, dim.framework)
            )
        else:
            used.add(dim.framework)
    if report.risk.framework not in VALID_FRAMEWORKS:
        reasons.append("risk screen cites unknown framework '%s'" % report.risk.framework)
    # The harness must triangulate - require at least two distinct frameworks.
    if len(used) < 2:
        reasons.append(
            "triangulation requires >=2 distinct frameworks, found %d (%s)"
            % (len(used), sorted(used))
        )
    if reasons:
        return GateResult("framework", False, reasons)
    return GateResult("framework", True)


def challenge_gate(report: ValuationReport) -> GateResult:
    """A devil's-advocate pass has stress-tested the recommendation."""
    reasons: List[str] = []
    if len(report.challenges) < MIN_CHALLENGES:
        reasons.append(
            "need >=%d devil's-advocate challenges, found %d" % (MIN_CHALLENGES, len(report.challenges))
        )
    # Each challenge must be a non-trivial string (>= 8 chars) to avoid filler.
    for i, c in enumerate(report.challenges):
        if len(c.strip()) < 8:
            reasons.append("challenge #%d is too short to be substantive" % i)
    if reasons:
        return GateResult("challenge", False, reasons)
    return GateResult("challenge", True)


def run_all_gates(report: ValuationReport) -> Tuple[bool, List[GateResult]]:
    """Run all three gates; return (overall, per-gate results)."""
    results = [evidence_gate(report), framework_gate(report), challenge_gate(report)]
    overall = all(r.passed for r in results)
    return overall, results


@dataclass
class ScopeDecision:
    outcome: Outcome
    message: str


def refuse_out_of_scope(report: ValuationReport) -> ScopeDecision:
    """Deterministic scope/refusal rule used before synthesis."""
    if report.outcome == Outcome.REFUSE:
        return ScopeDecision(Outcome.REFUSE, "Request refused: out of scope or unsafe.")
    if not report.risk.in_scope:
        return ScopeDecision(Outcome.REFUSE, "Risk screen flagged out-of-scope; refusing to value.")
    ok, _ = run_all_gates(report)
    if not ok and report.outcome == Outcome.PROCEED:
        return ScopeDecision(
            Outcome.DEGRADE,
            "Gates failed but scope is valid; degrading to a confidence-limited deliverable.",
        )
    return ScopeDecision(report.outcome, "Proceeding.")
