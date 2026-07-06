"""test_schemas.py - schema validation + serialisation round-trips."""
import json
import os

import pytest

from vav import schemas as S
from vav.schemas import (AssetProfile, AssetType, Evidence, EvidenceTier,
                         Outcome, RiskScreen, ScoredDimension, ValuationReport,
                         ValidationError, from_json, to_json)


def _good_profile():
    return AssetProfile(AssetType.NFT, S.ValuationPurpose.LISTING,
                        {"contract": "0x1", "token_id": "1"}, "minted 2021",
                        "PFP", notes="x")


def _good_evidence():
    return Evidence("claim", "src", "https://x.test", EvidenceTier.PRIMARY_MARKET_DATA,
                    "comparable_sales_with_liquidity_adjustment", "2026-07-06")


def _good_report():
    p = _good_profile()
    r = RiskScreen("risk_discounting_platform_custody_regulatory", True, 0.1, 0.1, 0.1, 0.1, 0.1,
                   [], "ok", [_good_evidence()])
    d = ScoredDimension("comparable_sales_with_liquidity_adjustment", "comps",
                        100, 80, 120, 0.6, 0.7, [_good_evidence()])
    d2 = ScoredDimension("income_approach", "income", 90, 70, 110, 0.4, 0.6, [_good_evidence()])
    from vav.schemas import RoadmapItem
    return ValuationReport(p, r, [d, d2], [RoadmapItem("act", 2, 5, "why")],
                           95, 75, 115, 0.65, ["challenge one", "challenge two"], ["lim"],
                           Outcome.PROCEED)


def test_profile_requires_identifiers():
    with pytest.raises(ValidationError):
        AssetProfile(AssetType.DOMAIN, S.ValuationPurpose.APPRAISAL, {}, "p", "u").validate()


def test_dimension_point_outside_band_rejected():
    with pytest.raises(ValidationError):
        ScoredDimension("income_approach", "x", 100, 80, 90, 0.5, 0.5).validate()


def test_unknown_framework_rejected():
    with pytest.raises(ValidationError):
        ScoredDimension("ad_hoc", "x", 100, 80, 120, 0.5, 0.5).validate()


def test_roadmap_effort_bounds():
    from vav.schemas import RoadmapItem
    with pytest.raises(ValidationError):
        RoadmapItem("a", 0, 5, "r").validate()
    with pytest.raises(ValidationError):
        RoadmapItem("a", 2, 9, "r").validate()


def test_round_trip_json():
    rep = _good_report()
    s = to_json(rep)
    back = from_json(s)
    assert back.value_point == rep.value_point
    assert back.dimensions[0].framework == rep.dimensions[0].framework
    assert back.outcome == Outcome.PROCEED


def test_load_all_fixtures(fixtures_dir, fixture_names):
    for name in fixture_names:
        rep = S.load_fixture(os.path.join(fixtures_dir, name))
        rep.validate()
        assert rep.value_low <= rep.value_point <= rep.value_high


def test_evidence_tier_ordering():
    assert EvidenceTier.rank(EvidenceTier.PRIMARY_MARKET_DATA) > EvidenceTier.rank(EvidenceTier.BLOG)
    assert EvidenceTier.rank(EvidenceTier.SYSTEMATIC_REVIEW) > EvidenceTier.rank(EvidenceTier.RCT)
