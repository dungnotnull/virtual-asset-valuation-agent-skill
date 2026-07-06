"""test_risk.py - risk screening helpers."""
import pytest

from vav.risk import (custody_risk, platform_risk, regulatory_risk, risk_discount,
                       wash_trade_flag)


def test_wash_trade_round_trip_detected():
    transfers = [
        {"from": "0xA", "to": "0xB", "price": 10.0, "ts": 1},
        {"from": "0xB", "to": "0xA", "price": 10.1, "ts": 2},
        {"from": "0xA", "to": "0xB", "price": 10.2, "ts": 3},
        {"from": "0xB", "to": "0xC", "price": 35.0, "ts": 4},
    ]
    risk, flags = wash_trade_flag(transfers)
    assert risk > 0
    assert any("round-trip" in f for f in flags)


def test_wash_trade_empty_history():
    risk, flags = wash_trade_flag([])
    assert risk == 0.0
    assert flags


def test_custody_risk_bounds_and_factors():
    sc = custody_risk("self_custody")
    sc_ms = custody_risk("self_custody", multi_sig=True)
    assert 0.0 <= sc_ms <= sc <= 1.0
    ex = custody_risk("exchange")
    assert 0.0 <= ex <= 1.0


def test_platform_risk_unknown_marketplace_high():
    assert platform_risk("unknown", listed_age_days=10) > platform_risk("opensea", listed_age_days=3650)


def test_regulatory_risk_sanctioned_high():
    assert regulatory_risk("us", "nft", sanctioned=True) > regulatory_risk("us", "nft")


def test_risk_discount_in_scope_range():
    d = risk_discount(0.2, 0.2, 0.2, 0.2, in_scope=True)
    assert 0.0 <= d <= 1.0


def test_risk_discount_out_of_scope_full():
    assert risk_discount(0.1, 0.1, 0.1, 0.1, in_scope=False) == 1.0


def test_risk_discount_rejects_bad_inputs():
    with pytest.raises(ValueError):
        risk_discount(1.5, 0.1, 0.1, 0.1)
