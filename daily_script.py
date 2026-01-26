import os
import urllib.parse
from datetime import datetime, timezone

import requests
import yfinance as yf


DEFAULT_TICKERS = ["VRT", "COHR", "RRX", "MBLY", "MOD", "GDX", "TER", "FN", "CCJ", "XYL", "HMY", "SFFLY"]


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


def create_copyable_html_page(message_body: str) -> str:
    """Create an HTML page with copyable stock data."""
    from html import escape
    # Escape HTML special characters in the message body
    escaped_body = escape(message_body)
    
    html_content = f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Stock Data - Copy</title>
    <style>
        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            max-width: 600px;
            margin: 40px auto;
            padding: 20px;
            background: #f5f5f5;
        }}
        .container {{
            background: white;
            padding: 30px;
            border-radius: 10px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
        }}
        h1 {{
            margin-top: 0;
            color: #333;
        }}
        #stockData {{
            background: #f8f9fa;
            border: 2px solid #e0e0e0;
            border-radius: 5px;
            padding: 20px;
            font-family: 'Courier New', monospace;
            font-size: 16px;
            line-height: 1.8;
            white-space: pre-wrap;
            word-wrap: break-word;
            margin: 20px 0;
            user-select: all;
            -webkit-user-select: all;
        }}
        button {{
            background: #007bff;
            color: white;
            border: none;
            padding: 12px 24px;
            font-size: 16px;
            border-radius: 5px;
            cursor: pointer;
            margin-top: 10px;
        }}
        button:hover {{
            background: #0056b3;
        }}
        .copied {{
            background: #28a745 !important;
        }}
    </style>
</head>
<body>
    <div class="container">
        <h1>📊 Stock Data</h1>
        <p>Tap the text below to select all, then copy:</p>
        <div id="stockData">{escaped_body}</div>
        <button onclick="copyToClipboard()">📋 Copy to Clipboard</button>
        <p id="status" style="margin-top: 10px; color: #28a745; display: none;">✓ Copied!</p>
    </div>
    <script>
        function copyToClipboard() {{
            const text = document.getElementById('stockData').textContent;
            navigator.clipboard.writeText(text).then(function() {{
                const btn = document.querySelector('button');
                const status = document.getElementById('status');
                btn.classList.add('copied');
                btn.textContent = '✓ Copied!';
                status.style.display = 'block';
                setTimeout(function() {{
                    btn.classList.remove('copied');
                    btn.textContent = '📋 Copy to Clipboard';
                    status.style.display = 'none';
                }}, 2000);
            }});
        }}
    </script>
</body>
</html>"""
    return html_content


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
    
    # Create HTML page with copyable data
    html_page = create_copyable_html_page(message_body)
    # Encode as data URI
    html_encoded = urllib.parse.quote(html_page)
    click_url = f"data:text/html;charset=utf-8,{html_encoded}"

    try:
        resp = requests.post(
            f"https://ntfy.sh/{topic}",
            data=message_body.encode("utf-8"),
            # ntfy/HTTP headers must be latin-1; keep them ASCII-only to avoid encoding issues on Windows.
            headers={
                "Title": "Daily stock update",
                "Priority": "default",
                "Tags": "chart_with_upwards_trend,moneybag",
                "Click": click_url,
            },
            timeout=15,
        )
        resp.raise_for_status()
        print("Push notification sent successfully!")
    except Exception as e:
        print(f"Failed to send: {e}")


if __name__ == "__main__":
    send_push_notification()



