from __future__ import annotations

import os
from pathlib import Path


FALLBACK_TICKERS: list[str] = ["VRT", "COHR", "RRX", "MBLY", "MOD", "GDX", "TER", "FN", "CCJ", "XYL", "HMY", "FCX", "IEX"]


def parse_tickers(raw: str) -> list[str]:
    """
    Parse comma- and/or newline-separated tickers.
    - Ignores empty lines
    - Supports comments starting with '#'
    - De-dupes while preserving order
    """
    cleaned_lines: list[str] = []
    for line in raw.splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        # Inline comments
        if "#" in line:
            line = line.split("#", 1)[0].strip()
        if line:
            cleaned_lines.append(line)

    parts: list[str] = []
    for line in cleaned_lines:
        parts.extend([p.strip().upper() for p in line.replace("\n", ",").split(",")])
    parts = [p for p in parts if p]

    seen: set[str] = set()
    out: list[str] = []
    for t in parts:
        if t not in seen:
            seen.add(t)
            out.append(t)
    return out


def load_tickers_from_file(path: str | Path) -> list[str]:
    p = Path(path)
    if not p.exists() or not p.is_file():
        return []
    try:
        return parse_tickers(p.read_text(encoding="utf-8"))
    except Exception:
        return []


def get_default_tickers() -> list[str]:
    """
    Default tickers for the project (used when no env var override exists).
    Order of sources:
    1) tickers file (env TICKERS_FILE or ./tickers.txt)
    2) FALLBACK_TICKERS
    """
    tickers_file = os.environ.get("TICKERS_FILE", "tickers.txt")
    file_tickers = load_tickers_from_file(tickers_file)
    return file_tickers if file_tickers else list(FALLBACK_TICKERS)


