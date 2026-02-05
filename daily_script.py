import os
from datetime import datetime, timezone

import requests
import yfinance as yf

from tickers_config import get_default_tickers, parse_tickers
from portfolio_config import PORTFOLIO, Holding


def _get_last_price(ticker: str) -> float | None:
    """Fetch last price for a ticker (same logic as the Streamlit app)."""
    try:
        stock = yf.Ticker(ticker)

        # Prefer fast_info['last_price'], but fall back to history if needed
        price: float | None = None
        try:
            fast_info = getattr(stock, "fast_info", None)
            if fast_info and "last_price" in fast_info and fast_info["last_price"] is not None:
                price = float(fast_info["last_price"])
        except Exception:
            # ignore and fall back to history
            pass

        if price is None:
            hist = stock.history(period="5d", interval="1d", auto_adjust=False)
            if not hist.empty:
                price = float(hist["Close"].dropna().iloc[-1])

        return price
    except Exception:
        return None


def _format_line_with_pl(ticker: str, price: float) -> str:
    """
    Format one line for the notification.

    If the ticker exists in `PORTFOLIO` with an `avg_cost`, we also add
    the running P/L percentage relative to your cost basis.
    """
    holding: Holding | None = PORTFOLIO.get(ticker)

    if holding is not None and holding.avg_cost > 0:
        pl_pct = (price - holding.avg_cost) / holding.avg_cost * 100.0
        return f"{ticker}: ${price:.2f}  (P/L {pl_pct:+.2f}%)"

    # No config for this ticker – just show the price.
    return f"{ticker}: ${price:.2f}"


def build_message_body(tickers: list[str]) -> str:
    now = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    lines: list[str] = [f"Daily Stock Update ({now})", ""]

    for raw_ticker in tickers:
        t = raw_ticker.strip().upper()
        if not t:
            continue

        price = _get_last_price(t)
        if price is None:
            lines.append(f"{t}: Error")
        else:
            lines.append(_format_line_with_pl(t, price))

    return "\n".join(lines)


def create_pastebin_url(message_body: str) -> str | None:
    """Create a pastebin URL using dpaste.com API (no auth required)."""
    try:
        # Use dpaste.com API - free, no auth required
        resp = requests.post(
            "https://dpaste.com/api/v2/",
            data={
                "content": message_body,
                "lexer": "text",
                "expires": "7days",  # Keep for 7 days
            },
            timeout=10,
        )
        if resp.status_code == 201:
            # dpaste returns the URL in the response body
            paste_url = resp.text.strip()
            if paste_url.startswith("http"):
                return paste_url
        return None
    except Exception:
        return None


def send_push_notification() -> None:
    topic = os.environ.get("NTFY_TOPIC")
    if not topic:
        raise RuntimeError("Missing NTFY_TOPIC environment variable.")

    tickers_env = os.environ.get("TICKERS", "")
    tickers = parse_tickers(tickers_env) if tickers_env.strip() else get_default_tickers()

    message_body = build_message_body(tickers)
    
    # Create pastebin URL for copyable version
    paste_url = create_pastebin_url(message_body)
    
    # Build headers
    headers = {
        "Title": "Daily stock update",
        "Priority": "default",
        "Tags": "chart_with_upwards_trend,moneybag",
    }
    
    # Add Click header if pastebin URL was created successfully
    if paste_url:
        headers["Click"] = paste_url
        print(f"Created pastebin URL: {paste_url}")
    else:
        print("Warning: Could not create pastebin URL, notification sent without clickable link")

    try:
        resp = requests.post(
            f"https://ntfy.sh/{topic}",
            data=message_body.encode("utf-8"),
            # ntfy/HTTP headers must be latin-1; keep them ASCII-only to avoid encoding issues on Windows.
            headers=headers,
            timeout=15,
        )
        resp.raise_for_status()
        print("Push notification sent successfully!")
    except Exception as e:
        print(f"Failed to send: {e}")


if __name__ == "__main__":
    send_push_notification()



