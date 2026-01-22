import os
from datetime import datetime, timezone

import requests
import yfinance as yf


DEFAULT_TICKERS = ["VRT", "COHR", "RRX", "MBLY", "MOD", "GDX", "TER", "FN", "CCJ", "XYL", "HMY",]


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


def send_push_notification() -> None:
    topic = os.environ.get("NTFY_TOPIC")
    if not topic:
        raise RuntimeError("Missing NTFY_TOPIC environment variable.")

    tickers_env = os.environ.get("TICKERS", "")
    tickers = (
        [t.strip().upper() for t in tickers_env.replace("\n", ",").split(",") if t.strip()]
        if tickers_env.strip()
        else DEFAULT_TICKERS
    )

    message_body = build_message_body(tickers)

    try:
        resp = requests.post(
            f"https://ntfy.sh/{topic}",
            data=message_body.encode("utf-8"),
            # ntfy/HTTP headers must be latin-1; keep them ASCII-only to avoid encoding issues on Windows.
            headers={
                "Title": "Daily stock update",
                "Priority": "default",
                "Tags": "chart_with_upwards_trend,moneybag",
            },
            timeout=15,
        )
        resp.raise_for_status()
        print("Push notification sent successfully!")
    except Exception as e:
        print(f"Failed to send: {e}")


if __name__ == "__main__":
    send_push_notification()



