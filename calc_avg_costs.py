import yfinance as yf


DATA = {
    "VRT": 3.74,
    "IEX": 8.87,
    "FCX": -2.51,
    "CCJ": -14.25,
    "WDC": -0.55,
    "MBLY": -19.48,
    "RRX": 25.88,
}


def get_price(ticker: str) -> float | None:
    t = yf.Ticker(ticker)
    price = None
    try:
        fi = getattr(t, "fast_info", None)
        if fi and "last_price" in fi and fi["last_price"] is not None:
            price = float(fi["last_price"])
    except Exception:
        price = None

    if price is None:
        hist = t.history(period="5d", interval="1d", auto_adjust=False)
        if not hist.empty:
            price = float(hist["Close"].dropna().iloc[-1])

    return price


def main() -> None:
    for ticker, pl_pct in DATA.items():
        price = get_price(ticker)
        if price is None:
            print(f"{ticker}: price=N/A, avg_cost=N/A")
            continue
        avg_cost = price / (1 + pl_pct / 100.0)
        print(f"{ticker}: price={price:.4f}, avg_cost={avg_cost:.4f}")


if __name__ == "__main__":
    main()

