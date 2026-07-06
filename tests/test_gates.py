"""test_gates.py - the three quality gates + scope rule."""
import pytest

from vav.gates import (challenge_gate, evidence_gate, framework_gate,
                        refuse_out_of_scope, run_all_gates, MIN_CHALLENGES)
from vav.schemas import (Evidence, EvidenceTier, Outcome, RoadmapItem,
                         RiskScreen, ScoredDimension, ValuationReport,
                         AssetProfile, AssetType, ValuationPurpose as VP)


def _ev(tier=EvidenceTier.PRIMARY_MARKET_DATA, fw="comparable_sales_with_liquidity_adjustment", url="https://x.test"):
    return Evidence("c", "s", url, tier, fw, "2026-07-06")


def _rep(dim_evidence=True, challenges=None, frameworks=None, outcome=Outcome.PROCEED,
         in_scope=True, num_challenges=None):
    p = AssetProfile(AssetType.NFT, VP.LISTING, {"c": "1"}, "p", "u")
    frameworks = frameworks or ["comparable_sales_with_liquidity_adjustment", "income_approach"]
    evs = [_ev()] if dim_evidence else []
    dims = [ScoredDimension(fw, "d%d" % i, 100, 80, 120, 0.5, 0.7, list(evs))
            for i, fw in enumerate(frameworks)]
    r = RiskScreen("risk_discounting_platform_custody_regulatory", in_scope, 0.1, 0.1, 0.1, 0.1, 0.1,
                   [], "ok", [_ev()])
    n = num_challenges if num_challenges is not None else (len(challenges) if challenges else 0)
    challenges = challenges or []
    return ValuationReport(p, r, dims, [RoadmapItem("a", 2, 5, "w")], 95, 75, 115, 0.65,
                           challenges or ["challenge one x", "challenge two x"], ["lim"], outcome)


def test_evidence_gate_passes():
    assert evidence_gate(_rep()).passed


def test_evidence_gate_fails_low_tier():
    rep = _rep()
    for d in rep.dimensions:
        d.evidence[0] = Evidence("c", "s", "https://x.test", EvidenceTier.BLOG,
                                 "comparable_sales_with_liquidity_adjustment", "2026-07-06")
    assert not evidence_gate(rep).passed


def test_evidence_gate_fails_missing_evidence():
    rep = _rep(dim_evidence=False)
    assert not evidence_gate(rep).passed


def test_framework_gate_requires_two_frameworks():
    rep = _rep(frameworks=["comparable_sales_with_liquidity_adjustment"])
    assert not framework_gate(rep).passed


def test_framework_gate_rejects_unknown():
    rep = _rep(frameworks=["ad_hoc", "income_approach"])
    assert not framework_gate(rep).passed


def test_challenge_gate_minimum():
    rep = _rep(challenges=["challenge one x", "challenge two x"])
    assert challenge_gate(rep).passed
    rep2 = _rep(challenges=["short"], num_challenges=1)
    rep2.challenges = ["short"]
    assert not challenge_gate(rep2).passed


def test_run_all_gates_overall():
    ok, results = run_all_gates(_rep())
    assert ok and len(results) == 3


def test_refuse_out_of_scope_when_risk_flags():
    rep = _rep(in_scope=False, outcome=Outcome.REFUSE)
    decision = refuse_out_of_scope(rep)
    assert decision.outcome == Outcome.REFUSE


def test_degrade_when_gates_fail_but_in_scope():
    rep = _rep(challenges=[], num_challenges=0)
    rep.challenges = []  # force challenge gate to fail
    decision = refuse_out_of_scope(rep)
    assert decision.outcome == Outcome.DEGRADE


def test_all_fixtures_pass_gates(fixtures_dir, fixture_names):
    from vav.schemas import load_fixture
    for name in fixture_names:
        rep = load_fixture(__import__("os").path.join(fixtures_dir, name))
        ok, _ = run_all_gates(rep)
        assert ok, name
