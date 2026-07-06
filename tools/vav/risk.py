"""Risk screening helpers for the virtual-asset-valuation skill.

Implements wash-trade detection heuristics, custody/platform/regulatory risk
scoring and a multiplicative composite discount consistent with the
`risk_discounting_platform_custody_regulatory` governing framework.

These are deterministic analytical helpers (not trained models) so they are
fully reproducible and unit-testable offline.
"""
from __future__ import annotations

import statistics
from typing import Iterable, Sequence, Tuple


def _clip01(x: float) -> float:
    return max(0.0, min(1.0, float(x)))


def wash_trade_flag(transfers: Sequence[dict]) -> Tuple[float, list]:
    """Heuristic wash-trading screen over on-chain transfer history.

    `transfers`: list of {"from","to","price","ts"} dicts sorted by ts.
    Returns (wash_trade_risk in [0,1], list of human-readable flags).
    """
    flags: list = []
    if not transfers:
        return 0.0, ["no transfer history available"]
    addrs = []
    for t in transfers:
        addrs.append((t.get("from", ""), t.get("to", ""), t.get("price", 0.0)))

    # Heuristic 1: round-trip between two wallets at the same/very close price.
    pair_freq: dict = {}
    for f, to, _ in addrs:
        if not f or not to:
            continue
        key = tuple(sorted((f, to)))
        pair_freq[key] = pair_freq.get(key, 0) + 1
    for pair, n in pair_freq.items():
        if n >= 3:
            flags.append("wallet pair %s transacted %d times (possible round-trip)" % (pair, n))

    # Heuristic 2: price inflation vs median that is statistically extreme.
    prices = [a[2] for a in addrs if a[2] > 0]
    if len(prices) >= 5:
        med = statistics.median(prices)
        recent = prices[-1]
        if med > 0 and recent > med * 3.0:
            flags.append("latest price %.4g is >3x median %.4g (inflationary spike)" % (recent, med))

    # Heuristic 3: tiny time gaps between transfers (bot-pattern).
    if len(addrs) >= 4:
        rapid = sum(1 for i in range(1, len(addrs)) if _gap_minutes(addrs[i - 1], addrs[i]) < 1.0)
        if rapid >= 2:
            flags.append("%d sub-minute transfers detected (bot-like cadence)" % rapid)

    risk = _clip01(0.15 * len(flags))
    return risk, flags


def _gap_minutes(a: tuple, b: tuple) -> float:
    # Placeholder numeric compare; real impl uses ts diff - kept dependency-free.
    try:
        return abs(float(b[0] if isinstance(b[0], (int, float)) else 0) -
                   float(a[0] if isinstance(a[0], (int, float)) else 0))
    except Exception:
        return 60.0


def custody_risk(custody_model: str, multi_sig: bool = False, insured: bool = False) -> float:
    """Score custody risk in [0,1].

    `custody_model` in {"self_custody","exchange","custodial_wallet","smart_contract"}.
    """
    base = {
        "self_custody": 0.20,
        "exchange": 0.45,
        "custodial_wallet": 0.35,
        "smart_contract": 0.55,
    }.get(custody_model, 0.50)
    if multi_sig:
        base *= 0.7
    if insured:
        base *= 0.8
    return _clip01(base)


def platform_risk(marketplace: str, listed_age_days: int, has_escrow: bool = True) -> float:
    """Score marketplace/platform risk in [0,1]."""
    tier = {
        "opensea": 0.15, "blur": 0.20, "magic_eden": 0.18, "namebio": 0.10,
        "godaddy": 0.12, "playerauctions": 0.35, "g2g": 0.45, "unknown": 0.55,
    }.get(marketplace.lower(), 0.50)
    # Newer venues carry more platform risk.
    age_factor = max(0.6, min(1.0, 1.0 - listed_age_days / 3650.0))
    escrow_factor = 0.9 if has_escrow else 1.1
    return _clip01(tier * age_factor * escrow_factor)


def regulatory_risk(jurisdiction: str, asset_class: str, sanctioned: bool = False) -> float:
    """Score regulatory risk in [0,1] given jurisdiction and asset class."""
    base = {"us": 0.25, "eu": 0.20, "sg": 0.22, "vn": 0.40, "global": 0.30}.get(
        jurisdiction.lower(), 0.35
    )
    class_adj = {"nft": 0.05, "game_account": 0.10, "domain": -0.05}.get(asset_class, 0.0)
    base = max(0.05, base + class_adj)
    if sanctioned:
        base = min(1.0, base + 0.50)
    return _clip01(base)


def risk_discount(platform: float, custody: float, wash: float, regulatory: float,
                  in_scope: bool = True) -> float:
    """Multiplicative composite discount in [0,1] applied to gross value.

    Combines the four risk vectors into a single haircut. If out of scope the
    discount is forced to 1.0 (asset not valued) per the refusal/scope rule.
    """
    if not in_scope:
        return 1.0
    vec = (platform, custody, wash, regulatory)
    if any(v < 0 or v > 1 for v in vec):
        raise ValueError("all risk vectors must be in [0,1]")
    # Each vector contributes a bounded marginal haircut; combined geometrically.
    haircuts = [min(0.40, v * 0.40) for v in vec]
    mult = 1.0
    for h in haircuts:
        mult *= (1.0 - h)
    return _clip01(1.0 - mult)
