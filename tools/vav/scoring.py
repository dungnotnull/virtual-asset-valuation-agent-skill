"""Deterministic, framework-grounded scoring math for the virtual-asset-valuation
skill. Pure functions with no I/O so they are trivially unit-testable.

Grounded in the named governing frameworks:
  - comparable_sales_with_liquidity_adjustment
  - income_approach
  - rarity_scoring_trait_frequency
  - liquidity_floor_price_bid_ask_depth
  - intangible_asset_valuation_cost_market_income (cost band helper)
"""
from __future__ import annotations

import math
import statistics
from typing import Iterable, List, Sequence, Tuple


def _require_nonneg(x: float, name: str) -> float:
    if x < 0:
        raise ValueError("%s must be non-negative, got %r" % (name, x))
    return float(x)


def comparable_value(sales: Sequence[float], weights: Sequence[float] | None = None) -> Tuple[float, float, float]:
    """Comparable-sales (market) approach.

    Returns (point, low, high) where the band is the interquartile-like spread.
    `sales` are realised comparable transaction prices; optional `weights`
    (recency/quality weights, summing to <=1) allow weighted central tendency.
    """
    sales = [_require_nonneg(s, "sale") for s in sales]
    if not sales:
        raise ValueError("at least one comparable sale is required")
    if weights is None:
        point = statistics.median(sales)
    else:
        if len(weights) != len(sales):
            raise ValueError("weights length must match sales length")
        w = [_require_nonneg(x, "weight") for x in weights]
        total = sum(w)
        if total <= 0:
            raise ValueError("weights must sum to > 0")
        w = [x / total for x in w]
        point = sum(si * wi for si, wi in zip(sales, w))
    if len(sales) == 1:
        # Single comp: derive a symmetric 20% band as a conservative default.
        return point, point * 0.8, point * 1.2
    low = min(sales)
    high = max(sales)
    if low == high:
        spread = point * 0.10
        low, high = point - spread, point + spread
    return point, low, high


def income_value(period_cash_flows: Sequence[float], discount_rate: float, terminal_growth: float = 0.0,
                 periods: int | None = None) -> Tuple[float, float, float]:
    """Income approach: discounted cash flow with a Gordon terminal value.

    `period_cash_flows` are expected net cash flows per period (e.g. per year).
    `discount_rate` is the periodic discount rate (0.10 = 10%). `terminal_growth`
    is the perpetual growth applied to the last period's cash flow.
    """
    if not 0.0 <= discount_rate < 1.0:
        raise ValueError("discount_rate must be in [0,1)")
    if not 0.0 <= terminal_growth < discount_rate:
        raise ValueError("terminal_growth must be in [0, discount_rate)")
    cfs = list(period_cash_flows)
    n = periods if periods is not None else len(cfs)
    if n <= 0:
        raise ValueError("need at least one period of cash flow")
    pv = 0.0
    for i in range(n):
        cf = cfs[i] if i < len(cfs) else cfs[-1]
        pv += _require_nonneg(cf, "cash_flow") / ((1.0 + discount_rate) ** (i + 1))
    if terminal_growth > 0 and cfs:
        terminal = cfs[-1] * (1.0 + terminal_growth) / (discount_rate - terminal_growth)
        pv += terminal / ((1.0 + discount_rate) ** n)
    # Band: +/- 25% to reflect discount-rate uncertainty (standard DCF practice).
    return pv, pv * 0.75, pv * 1.25


def rarity_score(trait_counts: dict, subject_traits: dict, collection_size: int) -> float:
    """Statistical rarity scoring (trait-frequency / product-of-rarities).

    `trait_counts` maps trait_name -> {value: count_in_collection}.
    `subject_traits` maps trait_name -> value for the subject token.
    `collection_size` is total items in the collection.
    Returns a rarity score in [0,1] where 1 = maximally rare (unique traits).
    """
    if collection_size <= 0:
        raise ValueError("collection_size must be > 0")
    if not subject_traits:
        raise ValueError("subject_traits must not be empty")
    log_sum = 0.0
    for trait_name, value in subject_traits.items():
        counts = trait_counts.get(trait_name, {})
        c = counts.get(value, 0)
        if c <= 0:
            # Trait value not observed in collection -> treat as unique.
            p = 1.0 / collection_size
        else:
            p = c / collection_size
        if p <= 0 or p > 1:
            raise ValueError("invalid trait probability %r" % p)
        log_sum += math.log(p)
    # geometric mean probability of the trait combination
    gmean_p = math.exp(log_sum / len(subject_traits))
    # normalise: a token with all-common traits -> gmean_p ~1 -> score ~0;
    # unique token -> gmean_p ~1/N -> score ~1.
    return 1.0 - math.pow(gmean_p, 1.0 / 3.0)


def liquidity_adjustment(base_value: float, liquidity_score: float) -> float:
    """Apply a liquidity haircut. `liquidity_score` in [0,1] (1 = highly liquid)."""
    if not 0.0 <= liquidity_score <= 1.0:
        raise ValueError("liquidity_score must be in [0,1]")
    _require_nonneg(base_value, "base_value")
    # Illiquidity discount up to 35% (empirical NFT illiquidity haircuts).
    discount = (1.0 - liquidity_score) * 0.35
    return base_value * (1.0 - discount)


def bid_ask_depth_score(bid_depth: float, ask_depth: float, spread_bps: float) -> float:
    """Liquidity & floor-price bid-ask depth score in [0,1].

    Combines order-book depth and tightness of spread. `*_depth` are notional
    depth within ~2% of mid; `spread_bps` is the bid-ask spread in basis points.
    """
    if bid_depth < 0 or ask_depth < 0:
        raise ValueError("depths must be non-negative")
    if spread_bps < 0:
        raise ValueError("spread must be non-negative")
    depth = min(bid_depth, ask_depth)
    depth_component = 1.0 - math.exp(-depth / 10_000.0)  # saturates near depth~30k
    spread_component = math.exp(-spread_bps / 200.0)     # 200bps -> ~0.37
    return 0.5 * depth_component + 0.5 * spread_component


def triangulate_value(dimension_estimates: Iterable[Tuple[float, float, float, float]],
                      composite_discount: float = 0.0) -> Tuple[float, float, float]:
    """Combine multiple (point, low, high, weight) dimension estimates.

    Weights normalised to sum to 1; result is the weighted central tendency with
    a band derived from the convex combination of the per-dimension bands, then
    `composite_discount` is applied multiplicatively (risk-discounting framework).
    """
    items = list(dimension_estimates)
    if not items:
        raise ValueError("at least one dimension estimate is required")
    if not 0.0 <= composite_discount < 1.0:
        raise ValueError("composite_discount must be in [0,1)")
    total_w = sum(w for *_, w in items)
    if total_w <= 0:
        raise ValueError("weights must sum to > 0")
    point = sum(p * (w / total_w) for p, _, _, w in items)
    low = sum(l * (w / total_w) for _, l, _, w in items)
    high = sum(h * (w / total_w) for _, _, h, w in items)
    if low > point:
        low = point
    if high < point:
        high = point
    mult = 1.0 - composite_discount
    return point * mult, low * mult, high * mult


def confidence_band(dimension_confidences: Sequence[float], evidence_count: int,
                    online: bool = True) -> float:
    """Aggregate confidence in [0,1] from per-dimension confidences and evidence
    density, penalised when operating offline (graceful-degradation signal).
    """
    if not dimension_confidences:
        return 0.0
    base = statistics.fmean(dimension_confidences)
    # evidence density bonus, capped
    density = min(1.0, math.log1p(evidence_count) / math.log1p(8.0))
    online_factor = 1.0 if online else 0.85
    return max(0.0, min(1.0, (0.7 * base + 0.3 * density) * online_factor))
