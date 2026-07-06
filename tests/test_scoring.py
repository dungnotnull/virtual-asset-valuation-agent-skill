"""test_scoring.py - deterministic scoring math."""
import math

import pytest

from vav.scoring import (bid_ask_depth_score, comparable_value, confidence_band,
                          income_value, liquidity_adjustment, rarity_score,
                          triangulate_value)


def test_comparable_value_basic():
    point, low, high = comparable_value([100, 110, 120])
    assert point == 110
    assert low == 100 and high == 120


def test_comparable_single_sale_band():
    point, low, high = comparable_value([1000])
    assert low == 800 and high == 1200


def test_comparable_weighted():
    point, _, _ = comparable_value([100, 200], [3, 1])
    assert point == 125  # (100*0.75 + 200*0.25)


def test_income_value_positive():
    pv, low, high = income_value([100, 100, 100], 0.10)
    assert pv > 0
    assert low < pv < high


def test_income_value_rejects_bad_rate():
    with pytest.raises(ValueError):
        income_value([100], 1.5)


def test_rarity_score_monotone():
    trait_counts = {"bg": {"rare": 10, "common": 9990}}
    rare = rarity_score(trait_counts, {"bg": "rare"}, 10000)
    common = rarity_score(trait_counts, {"bg": "common"}, 10000)
    assert rare > common
    assert 0.0 <= rare <= 1.0 and 0.0 <= common <= 1.0


def test_liquidity_adjustment_haircut():
    assert liquidity_adjustment(100, 1.0) == 100
    assert liquidity_adjustment(100, 0.0) == pytest.approx(65.0)  # 35% max haircut


def test_bid_ask_depth_score_bounded():
    s = bid_ask_depth_score(50000, 50000, 10)
    assert 0.0 <= s <= 1.0
    # tighter spread + deeper book -> higher score
    assert s > bid_ask_depth_score(1000, 1000, 500)


def test_triangulate_value_weights_normalised():
    point, low, high = triangulate_value([(100, 90, 110, 2), (200, 180, 220, 2)], 0.0)
    assert point == 150
    assert low == 135 and high == 165


def test_triangulate_value_applies_discount():
    point, _, _ = triangulate_value([(100, 90, 110, 1)], 0.2)
    assert point == pytest.approx(80.0)


def test_confidence_band_offline_penalty():
    on = confidence_band([0.7, 0.7], 6, online=True)
    off = confidence_band([0.7, 0.7], 6, online=False)
    assert off < on
    assert 0.0 <= off <= 1.0
