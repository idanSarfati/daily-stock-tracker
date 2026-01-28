from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Iterable

import pandas as pd
import streamlit as st
import yfinance as yf

from tickers_config import get_default_tickers, parse_tickers


@dataclass(frozen=True)
class PriceResult:
    ticker: str
    last_price: float | None
    currency: str | None
    status: str  # "ok" or error message


def _price_from_history(ticker: yf.Ticker) -> float | None:
    # Fallback path if fast_info is missing/unreliable.
    try:
        hist = ticker.history(period="5d", interval="1d", auto_adjust=False)
        if hist is None or hist.empty:
            return None
        return float(hist["Close"].dropna().iloc[-1])
    except Exception:
        return None


def get_last_price(ticker_str: str) -> PriceResult:
    t = ticker_str.strip().upper()
    if not t:
        return PriceResult(ticker=ticker_str, last_price=None, currency=None, status="empty ticker")

    try:
        ticker = yf.Ticker(t)
        price: float | None = None
        currency: str | None = None

        # Preferred: fast_info (often fastest/cleanest when available).
        try:
            fi = getattr(ticker, "fast_info", None)
            if fi:
                currency = fi.get("currency") if hasattr(fi, "get") else None
                # yfinance uses snake_case keys like 'last_price'
                price_val = fi.get("last_price") if hasattr(fi, "get") else None
                if price_val is not None:
                    price = float(price_val)
        except Exception:
            # Ignore and fall back to history.
            pass

        if price is None:
            price = _price_from_history(ticker)

        if price is None or not pd.notna(price):
            return PriceResult(ticker=t, last_price=None, currency=currency, status="invalid ticker or no data")

        return PriceResult(ticker=t, last_price=float(price), currency=currency, status="ok")
    except Exception as e:
        return PriceResult(ticker=t, last_price=None, currency=None, status=f"error: {type(e).__name__}")


def fetch_prices(tickers: Iterable[str]) -> pd.DataFrame:
    results: list[PriceResult] = [get_last_price(t) for t in tickers]
    df = pd.DataFrame(
        [
            {
                "ticker": r.ticker,
                "last_price": (round(r.last_price, 4) if r.last_price is not None else None),
                "currency": r.currency,
                "status": r.status,
            }
            for r in results
        ]
    )
    return df


def format_copy_block(df: pd.DataFrame) -> str:
    lines: list[str] = []
    for _, row in df.iterrows():
        t = str(row["ticker"])
        if row["status"] == "ok" and pd.notna(row["last_price"]):
            lines.append(f"{t}: ${row['last_price']}")
        else:
            lines.append(f"{t}: N/A ({row['status']})")
    return "\n".join(lines)


st.set_page_config(page_title="Stocks Watchlist", layout="centered")
st.title("Stocks Watchlist")
st.caption("Paste tickers (comma and/or newline separated) to fetch latest prices via yfinance.")

raw = st.text_area("Stock tickers", value=", ".join(get_default_tickers()), height=120)
tickers = parse_tickers(raw)

col1, col2 = st.columns([1, 2])
with col1:
    fetch = st.button("Fetch prices", type="primary", use_container_width=True)
with col2:
    st.write(f"Tickers parsed: **{len(tickers)}**")

if fetch:
    if not tickers:
        st.warning("Please enter at least one ticker.")
    else:
        with st.spinner("Fetching prices..."):
            df = fetch_prices(tickers)

        now = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
        st.subheader(f"Results ({now})")
        st.dataframe(df, use_container_width=True, hide_index=True)

        st.subheader("Copy-friendly output")
        st.code(format_copy_block(df), language="text")


