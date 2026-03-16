from __future__ import annotations

from dataclasses import dataclass
from typing import Dict


@dataclass(frozen=True)
class Holding:
    """
    Configuration for a single holding in your portfolio.

    Only `avg_cost` is required for calculating P/L %.
    - `avg_cost` is your average buy price **per share** (the same value
      your broker usually shows).
    - `shares` is optional and can be used later if you want absolute
      profit/loss in currency units.
    """

    ticker: str
    avg_cost: float  # average cost per share
    shares: float | None = None  # number of shares you hold (optional)


# ---------------------------------------------------------------------------
# HOW TO FILL THIS FOR YOUR PORTFOLIO
# ---------------------------------------------------------------------------
# For each ticker you own, add an entry to `PORTFOLIO` with:
#   - `ticker`: the symbol (uppercase)
#   - `avg_cost`: your average cost per share
#
# You can usually copy `avg_cost` directly from your broker.
#
# If you only know:
#   - total worth today (W)
#   - current P/L % (P, as a percentage, e.g. 3.74 for +3.74%)
#   - number of shares (N)
# you can compute:
#   invested_total = W / (1 + P / 100)
#   avg_cost = invested_total / N
#
# Example (numbers here are placeholders – replace with your real values):
#
#   "VRT": Holding(ticker="VRT", avg_cost=XXX.XX),
#   "IEX": Holding(ticker="IEX", avg_cost=YYY.YY),
#
# Using your snapshot (for reference only):
#   VRT: worth 342.32, P/L +3.74%
#   IEX: worth 212.25, P/L +8.87%
#   FCX: worth 146.23, P/L -2.51%
#   CCJ: worth  60.02, P/L -14.25%
#   WDC: worth  49.71, P/L -0.55%
#   MBLY: worth  3.76, P/L -19.48%
# Once you know the number of shares for each, you can compute avg_cost
# using the formula above and plug it in here.
#
# Until you fill a ticker here, the script will still work – it will just
# skip the P/L % column for that ticker.
# ---------------------------------------------------------------------------


PORTFOLIO: Dict[str, Holding] = {
    # Snapshot as of 2026‑03‑15, based on your current broker view.
    # avg_cost values are your purchase prices per share and `shares`
    # is the quantity currently held.
    "VRT": Holding(ticker="VRT", avg_cost=175.99, shares=1.2111),
    "CRWD": Holding(ticker="CRWD", avg_cost=422.47, shares=0.4165),
    "LEU": Holding(ticker="LEU", avg_cost=223.20, shares=0.6906),
    "BE": Holding(ticker="BE", avg_cost=153.40, shares=1.0),
    "ANET": Holding(ticker="ANET", avg_cost=130.67, shares=1.423),
}