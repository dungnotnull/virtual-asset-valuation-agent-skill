"""Harness orchestration contract + offline dry-run validator.

The markdown harness in `skills/main.md` is the prompt-side description of this
orchestration. This module codifies the step order, the gate enforcement and a
deterministic `run_dry` that validates a fully-built `ValuationReport` against
all gates WITHOUT invoking an LLM. This is what the pytest regression suite and
any production caller use to verify a synthesised report before delivery.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Callable, List, Optional, Tuple

from .gates import GateResult, refuse_out_of_scope, run_all_gates
from .knowledge import Brain
from .schemas import Outcome, ValuationReport


class HarnessStep(str, Enum):
    INTAKE = "sub-profile-intake"
    SCREEN = "sub-risk-screener"
    SCORE = "sub-scoring-engine"
    MARKET = "sub-market-data-updater"
    ROADMAP = "sub-improvement-roadmap"
    SYNTHESIZE = "synthesize"


STEP_ORDER: Tuple[HarnessStep, ...] = (
    HarnessStep.INTAKE,
    HarnessStep.SCREEN,
    HarnessStep.SCORE,
    HarnessStep.MARKET,
    HarnessStep.ROADMAP,
    HarnessStep.SYNTHESIZE,
)


@dataclass
class HarnessResult:
    step: HarnessStep
    gate_results: List[GateResult] = field(default_factory=list)
    scope_ok: bool = True
    scope_message: str = ""
    outcome: Outcome = Outcome.PROCEED
    report: Optional[ValuationReport] = None

    @property
    def gates_passed(self) -> bool:
        return all(g.passed for g in self.gate_results)


class Harness:
    """Codifies the harness contract from skills/main.md.

    Callers register step callbacks (the prompt-side sub-skills). For the
    production LLM-driven run the callbacks invoke the Skill tool; for the
    offline dry-run we supply a builder that hands back a prebuilt report.
    """

    def __init__(self, brain_path: Optional[str] = None):
        self.brain = Brain(brain_path) if brain_path else Brain()
        self._callbacks: dict = {}

    def register(self, step: HarnessStep, fn: Callable[..., object]) -> "Harness":
        self._callbacks[step] = fn
        return self

    def knowledge_refresh_needed(self, threshold_days: int = 7) -> bool:
        return self.brain.is_stale(threshold_days)

    def run(self, report: ValuationReport) -> HarnessResult:
        """Validate a synthesised report through scope + all three gates."""
        report.validate()
        scope = refuse_out_of_scope(report)
        ok, gate_results = run_all_gates(report)
        return HarnessResult(
            step=HarnessStep.SYNTHESIZE,
            gate_results=gate_results,
            scope_ok=scope.outcome != Outcome.REFUSE,
            scope_message=scope.message,
            outcome=scope.outcome,
            report=report if ok and scope.outcome != Outcome.REFUSE else None,
        )


def run_dry(report: ValuationReport) -> Tuple[bool, HarnessResult]:
    """Offline validation used by tests and any pre-delivery check."""
    harness = Harness()
    result = harness.run(report)
    return result.gates_passed and result.scope_ok, result
