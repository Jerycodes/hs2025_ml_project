"""Downloader fuer EURUSD-News via EODHD API."""

from __future__ import annotations

import argparse
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Iterator

import requests

from src.utils.io import DATA_RAW

API_URL = "https://eodhd.com/api/news"
DEFAULT_SYMBOL = "EURUSD.FOREX"
OUT_DIR = DATA_RAW / "news"
OUT_DIR.mkdir(parents=True, exist_ok=True)


def fetch_news(
    api_token: str,
    symbol: str,
    start: datetime,
    end: datetime,
    batch_size: int = 100,
) -> Iterator[dict]:
    """Iteriert ueber alle News-Items fuer den Zeitraum."""
    params = {
        "api_token": api_token,
        "s": symbol,
        "offset": 0,
        "limit": batch_size,
        "from": start.strftime("%Y-%m-%d"),
        "to": end.strftime("%Y-%m-%d"),
    }

    while True:
        resp = requests.get(API_URL, params=params, timeout=30)
        resp.raise_for_status()
        data = resp.json()
        if not data:
            break
        for item in data:
            yield item
        params["offset"] += batch_size


def write_jsonl(items: Iterator[dict], out_path: Path) -> None:
    """Speichert jede News als einzelne JSON-Zeile."""
    import json

    with out_path.open("w", encoding="utf-8") as fh:
        for obj in items:
            fh.write(json.dumps(obj) + "\n")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="EODHD News laden.")
    parser.add_argument("--token", type=str, default=os.getenv("EODHD_TOKEN"))
    parser.add_argument("--symbol", type=str, default=DEFAULT_SYMBOL)
    parser.add_argument("--start", type=str, default="2015-01-01")
    parser.add_argument(
        "--end",
        type=str,
        default=datetime.now(tz=timezone.utc).strftime("%Y-%m-%d"),
    )
    parser.add_argument(
        "--output",
        type=str,
        default=str(OUT_DIR / "eodhd_news.jsonl"),
    )
    parser.add_argument("--limit", type=int, default=100)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    if not args.token:
        raise ValueError("API-Token fehlt. Entweder --token setzen oder EODHD_TOKEN exportieren.")
    start_dt = datetime.fromisoformat(args.start)
    end_dt = datetime.fromisoformat(args.end)
    items = fetch_news(
        api_token=args.token,
        symbol=args.symbol,
        start=start_dt,
        end=end_dt,
        batch_size=args.limit,
    )
    write_jsonl(items, Path(args.output))


if __name__ == "__main__":
    main()
