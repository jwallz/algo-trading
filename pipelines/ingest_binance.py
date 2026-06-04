"""
Binance Historical Klines Ingester
===================================
Pulls OHLCV bar data from Binance's public REST API (no API key required)
and writes it to a NautilusTrader ParquetDataCatalog.

Usage:
    python pipelines/ingest_binance.py

Output:
    data/catalog/ — ParquetDataCatalog readable by NautilusTrader backtests
"""

import time
from datetime import datetime, timezone
from decimal import Decimal
from pathlib import Path

import pandas as pd
import requests
from nautilus_trader.model.data import Bar, BarType
from nautilus_trader.model.enums import AggregationSource, BarAggregation, PriceType
from nautilus_trader.model.identifiers import InstrumentId, Symbol, Venue
from nautilus_trader.model.objects import Price, Quantity
from nautilus_trader.persistence.catalog import ParquetDataCatalog
from nautilus_trader.persistence.wranglers import BarDataWrangler

# ── Configuration ──────────────────────────────────────────────────────────────
SYMBOL = "BTCUSDT"
VENUE = "BINANCE"
INTERVAL = "1h"          # Binance interval string
START_DATE = "2024-01-01"
END_DATE   = "2024-12-31"
PRICE_PRECISION = 2
SIZE_PRECISION  = 6
CATALOG_PATH = Path(__file__).parent.parent / "data" / "catalog"

# ── Binance API ────────────────────────────────────────────────────────────────
BINANCE_KLINES_URL = "https://api.binance.us/api/v3/klines"
MAX_BARS_PER_REQUEST = 1000  # Binance limit


def fetch_klines(symbol: str, interval: str, start_ms: int, end_ms: int) -> list:
    """Fetch all klines in [start_ms, end_ms] using paginated requests."""
    all_klines = []
    current_start = start_ms

    while current_start < end_ms:
        params = {
            "symbol": symbol,
            "interval": interval,
            "startTime": current_start,
            "endTime": end_ms,
            "limit": MAX_BARS_PER_REQUEST,
        }
        resp = requests.get(BINANCE_KLINES_URL, params=params, timeout=30)
        resp.raise_for_status()
        klines = resp.json()

        if not klines:
            break

        all_klines.extend(klines)
        print(f"  Fetched {len(all_klines)} bars so far... "
              f"(up to {datetime.fromtimestamp(klines[-1][0] / 1000, tz=timezone.utc).date()})")

        # Next page starts after the last bar's open time
        current_start = klines[-1][0] + 1

        if len(klines) < MAX_BARS_PER_REQUEST:
            break  # No more pages

        time.sleep(0.2)  # Be polite to the API

    return all_klines


def klines_to_dataframe(klines: list) -> pd.DataFrame:
    """Convert raw Binance kline list to a DataFrame NautilusTrader expects."""
    df = pd.DataFrame(klines, columns=[
        "open_time", "open", "high", "low", "close", "volume",
        "close_time", "quote_volume", "trades",
        "taker_buy_base", "taker_buy_quote", "ignore",
    ])
    df["timestamp"] = pd.to_datetime(df["open_time"], unit="ms", utc=True)
    df = df.set_index("timestamp")
    df = df[["open", "high", "low", "close", "volume"]].astype(float)
    return df


def main():
    print(f"Ingesting {SYMBOL} {INTERVAL} bars from {START_DATE} to {END_DATE}")

    start_ms = int(datetime.fromisoformat(START_DATE).replace(tzinfo=timezone.utc).timestamp() * 1000)
    end_ms   = int(datetime.fromisoformat(END_DATE).replace(tzinfo=timezone.utc).timestamp() * 1000)

    # ── Fetch ──────────────────────────────────────────────────────────────────
    print("\nFetching from Binance...")
    klines = fetch_klines(SYMBOL, INTERVAL, start_ms, end_ms)
    print(f"Total bars fetched: {len(klines)}")

    df = klines_to_dataframe(klines)
    print(df.head())

    # ── Build Instrument ───────────────────────────────────────────────────────
    from nautilus_trader.model.data import BarSpecification
    from nautilus_trader.model.instruments import CurrencyPair
    from nautilus_trader.model.currencies import BTC, USDT

    instrument_id = InstrumentId(Symbol(SYMBOL), Venue(VENUE))

    instrument = CurrencyPair(
        instrument_id=instrument_id,
        raw_symbol=Symbol(SYMBOL),
        base_currency=BTC,
        quote_currency=USDT,
        price_precision=PRICE_PRECISION,
        size_precision=SIZE_PRECISION,
        price_increment=Price(0.01, PRICE_PRECISION),
        size_increment=Quantity(0.000001, SIZE_PRECISION),
        lot_size=None,
        max_quantity=None,
        min_quantity=Quantity(0.00001, SIZE_PRECISION),
        max_notional=None,
        min_notional=None,
        max_price=None,
        min_price=None,
        margin_init=Decimal(0),
        margin_maint=Decimal(0),
        maker_fee=Decimal("0.001"),
        taker_fee=Decimal("0.001"),
        ts_event=0,
        ts_init=0,
    )

    # ── Build BarType ──────────────────────────────────────────────────────────
    bar_spec = BarSpecification(
        step=1,
        aggregation=BarAggregation.HOUR,
        price_type=PriceType.LAST,
    )
    bar_type = BarType(
        instrument_id=instrument_id,
        bar_spec=bar_spec,
        aggregation_source=AggregationSource.EXTERNAL,
    )

    # ── Convert to NautilusTrader Bars ─────────────────────────────────────────
    wrangler = BarDataWrangler(bar_type, instrument)
    bars = wrangler.process(df)
    print(f"\nConverted {len(bars)} NautilusTrader Bar objects")

    # ── Write to Catalog ───────────────────────────────────────────────────────
    CATALOG_PATH.mkdir(parents=True, exist_ok=True)
    catalog = ParquetDataCatalog(str(CATALOG_PATH))
    catalog.write_data(bars)
    print(f"\nCatalog written to: {CATALOG_PATH}")

    # ── Verify ─────────────────────────────────────────────────────────────────
    loaded = catalog.bars([bar_type])
    print(f"Verification: {len(loaded)} bars readable from catalog")
    print(f"Date range: {loaded[0].ts_init} → {loaded[-1].ts_init}")
    print("\nDone!")


if __name__ == "__main__":
    main()
