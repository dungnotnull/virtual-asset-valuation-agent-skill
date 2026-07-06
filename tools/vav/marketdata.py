"""Market-data adapter contracts for the virtual-asset-valuation skill.

Defines the canonical `MarketDataSnapshot` and `LiquidityMetrics` structures and
an `aggregate` reducer used by sub-market-data-updater. Real marketplace adapters
(OpenSea/Blur/NameBio/PlayerAuctions) plug into this contract; the contract itself
is I/O-free so it can be validated and tested deterministically.
"""
from __future__ import annotations

import statistics
from dataclasses import dataclass, field
from typing import List, Sequence


@dataclass
class LiquidityMetrics:
    floor_price: float
    median_sale: float
    bid_depth: float          # notional bid depth within ~2% of floor
    ask_depth: float
    spread_bps: float
    listings_7d: int
    sales_7d: int
    turnover_7d: float

    def validate(self) -> None:
        for name, v in (("floor_price", self.floor_price), ("median_sale", self.median_sale),
                        ("bid_depth", self.bid_depth), ("ask_depth", self.ask_depth),
                        ("turnover_7d", self.turnover_7d)):
            if v < 0:
                raise ValueError("%s must be non-negative" % name)
        if self.spread_bps < 0:
            raise ValueError("spread_bps must be non-negative")
        if self.listings_7d < 0 or self.sales_7d < 0:
            raise ValueError("counts must be non-negative")


@dataclass
class MarketDataSnapshot:
    source: str                       # e.g. "opensea", "blur", "namebio"
    asset_ref: str                    # contract+token_id / domain / account_id
    retrieved_at: str                 # ISO-8601
    sales: List[float] = field(default_factory=list)
    liquidity: LiquidityMetrics | None = None

    def validate(self) -> None:
        if not self.source.strip():
            raise ValueError("source must not be empty")
        if not self.asset_ref.strip():
            raise ValueError("asset_ref must not be empty")
        for s in self.sales:
            if s < 0:
                raise ValueError("sales must be non-negative")
        if self.liquidity is not None:
            self.liquidity.validate()


def aggregate(snapshots: Sequence[MarketDataSnapshot]) -> MarketDataSnapshot:
    """Reduce a set of snapshots into a single composite snapshot.

    Used by sub-market-data-updater to fuse data across marketplaces. Sales are
    pooled; liquidity metrics are medians (robust to outliers / wash trades).
    """
    if not snapshots:
        raise ValueError("at least one snapshot is required")
    pooled: List[float] = []
    floors, medians, bids, asks, spreads, listings, sales_n, turnovers = ([] for _ in range(8))
    for s in snapshots:
        s.validate()
        pooled.extend(s.sales)
        if s.liquidity is not None:
            floors.append(s.liquidity.floor_price)
            medians.append(s.liquidity.median_sale)
            bids.append(s.liquidity.bid_depth)
            asks.append(s.liquidity.ask_depth)
            spreads.append(s.liquidity.spread_bps)
            listings.append(s.liquidity.listings_7d)
            sales_n.append(s.liquidity.sales_7d)
            turnovers.append(s.liquidity.turnover_7d)

    def med(seq: List[float], default: float = 0.0) -> float:
        return statistics.median(seq) if seq else default

    liq = LiquidityMetrics(
        floor_price=med(floors),
        median_sale=med(medians),
        bid_depth=med(bids),
        ask_depth=med(asks),
        spread_bps=med(spreads),
        listings_7d=int(med(listings)),
        sales_7d=int(med(sales_n)),
        turnover_7d=med(turnovers),
    )
    return MarketDataSnapshot(
        source="aggregate(%d)" % len(snapshots),
        asset_ref=snapshots[0].asset_ref,
        retrieved_at=max(s.retrieved_at for s in snapshots),
        sales=pooled,
        liquidity=liq,
    )
