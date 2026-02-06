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
    # These avg_cost values were derived on 2026‑02‑05 from
    # current market prices (via yfinance) and your reported
    # P/L% for each holding. They are approximate but will
    # keep your running P/L% very close to what your broker shows.
    "VRT": Holding(ticker="VRT", avg_cost=175.9784),
    "IEX": Holding(ticker="IEX", avg_cost=194.9573),
    "FCX": Holding(ticker="FCX", avg_cost=63.4527),
    "CCJ": Holding(ticker="CCJ", avg_cost=133.9009),
    "WDC": Holding(ticker="WDC", avg_cost=270.9000),
    "MBLY": Holding(ticker="MBLY", avg_cost=11.0904),
    "RRX": Holding(ticker="RRX", avg_cost=158.8815),
}

