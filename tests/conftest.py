# conftest.py - shared pytest config + import path for the vav package.
import os, sys
ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, os.path.join(ROOT, "tools"))

import pytest

FIXTURES = os.path.join(ROOT, "tests", "fixtures")


@pytest.fixture(scope="session")
def fixtures_dir():
    return FIXTURES


@pytest.fixture(scope="session")
def fixture_names():
    return [
        "scenario_1_domain.json",
        "scenario_2_nft_rarity.json",
        "scenario_3_game_account.json",
        "scenario_4_wash_trading.json",
        "scenario_5_market_shift.json",
        "scenario_6_sell_timing.json",
    ]
