from __future__ import annotations

import os
import smtplib
from dataclasses import dataclass
from datetime import datetime, timezone
from email.message import EmailMessage
from typing import Iterable

import pandas as pd
import yfinance as yf


DEFAULT_TICKERS = ["VRT", "COHR", "RRX", "MBLY", "MOD", "GDX", "TER", "FN", "CCJ", "XYL", "HMY", "SFFLY"]


@dataclass(frozen=True)
class PriceResult:
    ticker: str
    last_price: float | None
    currency: str | None
    status: str  # "ok" or error message


def _price_from_history(ticker: yf.Ticker) -> float | None:
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

        try:
            fi = getattr(ticker, "fast_info", None)
            if fi:
                currency = fi.get("currency") if hasattr(fi, "get") else None
                price_val = fi.get("last_price") if hasattr(fi, "get") else None
                if price_val is not None:
                    price = float(price_val)
        except Exception:
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
    return pd.DataFrame(
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


def format_results(df: pd.DataFrame) -> str:
    now = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    lines: list[str] = [f"Daily Stock Update ({now})", ""]
    for _, row in df.iterrows():
        t = str(row["ticker"])
        if row["status"] == "ok" and pd.notna(row["last_price"]):
            lines.append(f"{t}: ${row['last_price']}")
        else:
            lines.append(f"{t}: N/A ({row['status']})")
    return "\n".join(lines)


def send_email(body: str) -> None:
    email_user = os.environ.get("EMAIL_USER")
    email_password = os.environ.get("EMAIL_PASSWORD")
    if not email_user or not email_password:
        raise RuntimeError("Missing EMAIL_USER and/or EMAIL_PASSWORD environment variables.")

    smtp_server = os.environ.get("SMTP_SERVER", "smtp.gmail.com")
    smtp_port = int(os.environ.get("SMTP_PORT", "465"))

    msg = EmailMessage()
    msg["Subject"] = "Daily Stock Update"
    msg["From"] = email_user
    msg["To"] = email_user
    msg.set_content(body)

    with smtplib.SMTP_SSL(smtp_server, smtp_port) as server:
        server.login(email_user, email_password)
        server.send_message(msg)


def main() -> None:
    tickers_env = os.environ.get("TICKERS", "")
    tickers = (
        [t.strip().upper() for t in tickers_env.replace("\n", ",").split(",") if t.strip()]
        if tickers_env.strip()
        else DEFAULT_TICKERS
    )

    df = fetch_prices(tickers)
    body = format_results(df)
    send_email(body)


if __name__ == "__main__":
    main()


