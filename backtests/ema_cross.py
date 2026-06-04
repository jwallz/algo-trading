"""
EMA Cross Backtest
==================
A simple dual-EMA crossover strategy backtested against 2024 BTCUSDT 1h bars
loaded from the local ParquetDataCatalog.

Strategy logic:
  - Go LONG  when fast EMA crosses ABOVE slow EMA
  - Go SHORT when fast EMA crosses BELOW slow EMA
  - Always in the market (no flat periods)

Usage:
    python backtests/ema_cross.py
"""

from decimal import Decimal
from pathlib import Path

import pandas as pd
from nautilus_trader.backtest.engine import BacktestEngine, BacktestEngineConfig
from nautilus_trader.config import LoggingConfig
from nautilus_trader.model.currencies import BTC, USDT
from nautilus_trader.model.data import Bar, BarSpecification, BarType
from nautilus_trader.model.enums import (
    AggregationSource,
    BarAggregation,
    OmsType,
    AccountType,
    PriceType,
)
from nautilus_trader.model.identifiers import InstrumentId, Symbol, TraderId, Venue
from nautilus_trader.model.instruments import CurrencyPair
from nautilus_trader.model.objects import Money, Price, Quantity
from nautilus_trader.persistence.catalog import ParquetDataCatalog
from nautilus_trader.trading.strategy import Strategy
from nautilus_trader.config import StrategyConfig
from nautilus_trader.model.orders import MarketOrder
from nautilus_trader.model.enums import OrderSide, TimeInForce

# ── Configuration ──────────────────────────────────────────────────────────────
CATALOG_PATH = Path(__file__).parent.parent / "data" / "catalog"
SYMBOL = "BTCUSDT"
VENUE_NAME = "BINANCE"
FAST_EMA = 10   # periods
SLOW_EMA = 30   # periods
TRADE_SIZE = Decimal("0.01")  # BTC per trade
STARTING_BALANCE_USDT = 10_000
PRICE_PRECISION = 2
SIZE_PRECISION = 6


# ── Strategy ───────────────────────────────────────────────────────────────────
class EmaCrossConfig(StrategyConfig, frozen=True):
    instrument_id: str
    bar_type: str
    fast_ema_period: int = 10
    slow_ema_period: int = 30
    trade_size: Decimal = Decimal("0.01")


class EmaCrossStrategy(Strategy):
    def __init__(self, config: EmaCrossConfig):
        super().__init__(config)
        self.instrument_id = InstrumentId.from_str(config.instrument_id)
        self.bar_type = BarType.from_str(config.bar_type)
        self.fast_period = config.fast_ema_period
        self.slow_period = config.slow_ema_period
        self.trade_size = config.trade_size

        self.closes: list[float] = []
        self.position_side = None  # "long" or "short"

    def on_start(self):
        self.instrument = self.cache.instrument(self.instrument_id)
        self.subscribe_bars(self.bar_type)

    def on_bar(self, bar: Bar):
        self.closes.append(float(bar.close))

        if len(self.closes) < self.slow_period + 1:
            return  # Not enough data yet

        fast_ema_prev = self._ema(self.closes[-(self.fast_period + 1):-1], self.fast_period)
        fast_ema_curr = self._ema(self.closes[-self.fast_period:], self.fast_period)
        slow_ema_prev = self._ema(self.closes[-(self.slow_period + 1):-1], self.slow_period)
        slow_ema_curr = self._ema(self.closes[-self.slow_period:], self.slow_period)

        bullish_cross = fast_ema_prev <= slow_ema_prev and fast_ema_curr > slow_ema_curr
        bearish_cross = fast_ema_prev >= slow_ema_prev and fast_ema_curr < slow_ema_curr

        if bullish_cross and self.position_side != "long":
            if self.position_side == "short":
                self.close_all_positions(self.instrument_id)
            self._enter_long()

        elif bearish_cross and self.position_side != "short":
            if self.position_side == "long":
                self.close_all_positions(self.instrument_id)
            self._enter_short()

    def _enter_long(self):
        order = self.order_factory.market(
            instrument_id=self.instrument_id,
            order_side=OrderSide.BUY,
            quantity=self.instrument.make_qty(self.trade_size),
            time_in_force=TimeInForce.GTC,
        )
        self.submit_order(order)
        self.position_side = "long"

    def _enter_short(self):
        order = self.order_factory.market(
            instrument_id=self.instrument_id,
            order_side=OrderSide.SELL,
            quantity=self.instrument.make_qty(self.trade_size),
            time_in_force=TimeInForce.GTC,
        )
        self.submit_order(order)
        self.position_side = "short"

    def _ema(self, values: list[float], period: int) -> float:
        if not values:
            return 0.0
        k = 2 / (period + 1)
        ema = values[0]
        for v in values[1:]:
            ema = v * k + ema * (1 - k)
        return ema

    def on_stop(self):
        self.close_all_positions(self.instrument_id)


# ── Build Instrument ───────────────────────────────────────────────────────────
def build_instrument(instrument_id: InstrumentId) -> CurrencyPair:
    return CurrencyPair(
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


# ── Main ───────────────────────────────────────────────────────────────────────
def main():
    venue = Venue(VENUE_NAME)
    instrument_id = InstrumentId(Symbol(SYMBOL), venue)
    instrument = build_instrument(instrument_id)

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

    # ── Load data from catalog ─────────────────────────────────────────────────
    print("Loading bars from catalog...")
    catalog = ParquetDataCatalog(str(CATALOG_PATH))
    bars = catalog.bars([bar_type])
    print(f"Loaded {len(bars)} bars")

    # ── Configure engine ───────────────────────────────────────────────────────
    engine = BacktestEngine(
        config=BacktestEngineConfig(
            trader_id=TraderId("BACKTESTER-001"),
            logging=LoggingConfig(log_level="WARNING"),
        )
    )

    engine.add_venue(
        venue=venue,
        oms_type=OmsType.NETTING,
        account_type=AccountType.MARGIN,
        base_currency=USDT,
        starting_balances=[Money(STARTING_BALANCE_USDT, USDT)],
    )

    engine.add_instrument(instrument)
    engine.add_data(bars)

    # ── Configure strategy ─────────────────────────────────────────────────────
    strategy_config = EmaCrossConfig(
        instrument_id=str(instrument_id),
        bar_type=str(bar_type),
        fast_ema_period=FAST_EMA,
        slow_ema_period=SLOW_EMA,
        trade_size=TRADE_SIZE,
    )
    strategy = EmaCrossStrategy(config=strategy_config)
    engine.add_strategy(strategy)

    # ── Run ────────────────────────────────────────────────────────────────────
    print(f"\nRunning EMA Cross backtest (EMA{FAST_EMA}/EMA{SLOW_EMA}) on 2024 BTCUSDT 1h...")
    engine.run()

    # ── Results ────────────────────────────────────────────────────────────────
    print("\n" + "=" * 60)
    print("BACKTEST RESULTS")
    print("=" * 60)

    stats = engine.trader.generate_account_report(venue)
    print(stats)

    order_fills = engine.trader.generate_order_fills_report()
    print(f"\nTotal fills: {len(order_fills)}")

    positions = engine.trader.generate_positions_report()
    print(f"Total positions: {len(positions)}")

    if len(positions) > 0:
        available = ["instrument_id", "entry", "avg_px_open", "avg_px_close", "realized_pnl"]
        cols = [c for c in available if c in positions.columns]
        print(positions[cols].tail(20).to_string())

        # Summary stats
        if "realized_pnl" in positions.columns:
            pnl = positions["realized_pnl"].astype(str).str.split().str[0].astype(float)
            print("\n── PnL Summary ──────────────────────────────")
            print(f"  Total trades   : {len(pnl)}")
            print(f"  Winners        : {(pnl > 0).sum()}")
            print(f"  Losers         : {(pnl < 0).sum()}")
            print(f"  Win rate       : {(pnl > 0).mean() * 100:.1f}%")
            print(f"  Total PnL      : {pnl.sum():.2f} USDT")
            print(f"  Avg win        : {pnl[pnl > 0].mean():.2f} USDT")
            print(f"  Avg loss       : {pnl[pnl < 0].mean():.2f} USDT")
            print(f"  Final balance  : {STARTING_BALANCE_USDT + pnl.sum():.2f} USDT")

    engine.dispose()
    print("\nDone!")


if __name__ == "__main__":
    main()
