import os
from datetime import datetime, timezone

import requests
import yfinance as yf

from tickers_config import get_default_tickers, parse_tickers


def build_message_body(tickers: list[str]) -> str:
    now = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    lines: list[str] = [f"Daily Stock Update ({now})", ""]

    for ticker in tickers:
        t = ticker.strip().upper()
        if not t:
            continue

        try:
            stock = yf.Ticker(t)

            # Prefer fast_info['last_price'], but fall back to history if needed
            price = None
            try:
                fast_info = getattr(stock, "fast_info", None)
                if fast_info and "last_price" in fast_info and fast_info["last_price"] is not None:
                    price = float(fast_info["last_price"])
            except Exception:
                pass

            if price is None:
                hist = stock.history(period="5d", interval="1d", auto_adjust=False)
                if not hist.empty:
                    price = float(hist["Close"].dropna().iloc[-1])

            if price is None:
                lines.append(f"{t}: Error")
            else:
                lines.append(f"{t}: ${price:.2f}")
        except Exception:
            lines.append(f"{t}: Error")

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



