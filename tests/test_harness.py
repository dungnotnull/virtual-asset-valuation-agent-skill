"""test_harness.py - harness orchestration + offline dry-run for all scenarios."""
import os

from vav.harness import Harness, HarnessStep, STEP_ORDER, run_dry
from vav.marketdata import MarketDataSnapshot, LiquidityMetrics, aggregate
from vav.schemas import load_fixture, Outcome


def test_step_order_matches_main_md():
    assert STEP_ORDER == (
        HarnessStep.INTAKE, HarnessStep.SCREEN, HarnessStep.SCORE,
        HarnessStep.MARKET, HarnessStep.ROADMAP, HarnessStep.SYNTHESIZE,
    )


def test_marketdata_aggregate_medians():
    a = MarketDataSnapshot("opensea", "0x1", "2026-07-06", [1, 2, 3],
                           LiquidityMetrics(10, 11, 100, 100, 20, 5, 3, 30))
    b = MarketDataSnapshot("blur", "0x1", "2026-07-07", [4, 5],
                           LiquidityMetrics(20, 21, 200, 200, 10, 7, 4, 40))
    agg = aggregate([a, b])
    assert agg.liquidity.floor_price == 15
    assert agg.asset_ref == "0x1"
    assert agg.retrieved_at == "2026-07-07"


def test_marketdata_aggregate_requires_input():
    import pytest
    with pytest.raises(ValueError):
        aggregate([])


def test_dry_run_passes_all_fixtures(fixtures_dir, fixture_names):
    for name in fixture_names:
        rep = load_fixture(os.path.join(fixtures_dir, name))
        ok, result = run_dry(rep)
        assert ok, (name, [g.name + ":" + str(g.reasons) for g in result.gate_results])
        assert result.scope_ok
        assert result.report is not None


def test_harness_refuse_flow():
    from vav.schemas import (AssetProfile, AssetType, ValuationPurpose as VP,
                             RiskScreen, ScoredDimension, Evidence, EvidenceTier,
                             RoadmapItem, ValuationReport)
    p = AssetProfile(AssetType.NFT, VP.LISTING, {"c": "1"}, "p", "u")
    r = RiskScreen("risk_discounting_platform_custody_regulatory", False, 0.1, 0.1, 0.1, 0.1, 0.1,
                   [], "out of scope", [])
    d = ScoredDimension("comparable_sales_with_liquidity_adjustment", "x", 100, 80, 120, 0.6, 0.7,
                       [Evidence("c", "s", "https://x.test", EvidenceTier.PRIMARY_MARKET_DATA,
                                 "comparable_sales_with_liquidity_adjustment", "2026-07-06")])
    d2 = ScoredDimension("income_approach", "y", 90, 70, 110, 0.4, 0.6,
                        [Evidence("c", "s", "https://x.test", EvidenceTier.PRIMARY_MARKET_DATA,
                                  "income_approach", "2026-07-06")])
    rep = ValuationReport(p, r, [d, d2], [RoadmapItem("a", 2, 5, "w")], 95, 75, 115, 0.6,
                          ["challenge one x", "challenge two x"], [], Outcome.REFUSE)
    ok, result = run_dry(rep)
    assert not ok
    assert not result.scope_ok


def test_knowledge_brain_helpers():
    from vav.knowledge import Brain, entry_hash, read_brain_hashes
    repo_root = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
    brain = Brain(os.path.join(repo_root, "SECOND-KNOWLEDGE-BRAIN.md"))
    assert brain.exists()
    assert entry_hash("https://x", "t") == entry_hash("https://X", "t")
    assert isinstance(read_brain_hashes(brain.path), set)
