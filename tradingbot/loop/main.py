# tradingbot/loop/main.py
import time
from datetime import datetime, timezone

from tradingbot.data.binance_feed import get_price, get_klines, PriceFetchError
from tradingbot.engine.db import init_db, insert_equity_point, insert_strategy_run, get_open_trades
from tradingbot.engine.portfolio import Portfolio
from tradingbot.engine.broker import Broker
from tradingbot.strategies.sma_cross import SmaCrossStrategy
from tradingbot.strategies.rsi import RsiStrategy
from tradingbot.strategies.momentum import MomentumStrategy
from tradingbot.backtest.runner import run_backtest
from tradingbot.sizing.kelly import position_size

SYMBOLS = ["BTCUSDT", "ETHUSDT", "SOLUSDT"]
POLL_SECONDS = 300
STARTING_CASH = 10000.0
DB_PATH = "tradingbot.db"

ALL_STRATEGIES = [SmaCrossStrategy(), RsiStrategy(), MomentumStrategy()]


def vet_strategies(conn):
    """Backtest each strategy per symbol on 1h history; only passing ones trade live."""
    approved = []
    for symbol in SYMBOLS:
        klines = get_klines(symbol, "1h", 500)
        closes = [k["close"] for k in klines]
        for strategy in ALL_STRATEGIES:
            result = run_backtest(strategy, closes)
            insert_strategy_run(
                conn, strategy=f"{strategy.name}:{symbol}", passed=result.passed,
                sharpe=result.sharpe, max_drawdown=result.max_drawdown, reason=result.reason,
                run_at=datetime.now(timezone.utc).isoformat(),
            )
            if result.passed:
                win_rate = 0.5  # placeholder win rate refined from live trade history over time
                payoff_ratio = max(result.total_pnl, 1.0) / STARTING_CASH * 10
                approved.append((symbol, strategy, win_rate, payoff_ratio))
    return approved


def run_cycle(conn, portfolio, broker, approved_strategies, price_history):
    now = datetime.now(timezone.utc).isoformat()
    current_prices = {}
    for symbol in SYMBOLS:
        try:
            price = get_price(symbol)
        except PriceFetchError as exc:
            print(f"[{now}] price fetch failed for {symbol}: {exc} — skipping symbol this cycle")
            continue
        current_prices[symbol] = price
        price_history.setdefault(symbol, []).append(price)

    for symbol, strategy, win_rate, payoff_ratio in approved_strategies:
        closes = price_history.get(symbol, [])
        if len(closes) < 2 or symbol not in current_prices:
            continue
        signal = strategy.signal(closes)
        has_open = symbol in portfolio.positions
        if signal == "buy" and not has_open:
            dollars = position_size(portfolio.cash, win_rate, payoff_ratio)
            if dollars <= 0:
                continue
            qty = dollars / current_prices[symbol]
            broker.open_trade(
                symbol=symbol, side="buy", qty=qty, market_price=current_prices[symbol],
                strategy=strategy.name, opened_at=now,
            )
        elif signal == "sell" and has_open:
            open_trades = [t for t in get_open_trades(conn) if t["symbol"] == symbol]
            if open_trades:
                broker.close_trade(
                    open_trades[0]["id"], symbol=symbol,
                    market_price=current_prices[symbol], closed_at=now,
                )

    equity = portfolio.equity(current_prices) if current_prices else portfolio.cash
    insert_equity_point(conn, timestamp=now, equity=equity)
    print(f"[{now}] equity={equity:.2f} cash={portfolio.cash:.2f} positions={list(portfolio.positions.keys())}")


def main():
    conn = init_db(DB_PATH)
    portfolio = Portfolio(cash=STARTING_CASH)
    broker = Broker(portfolio, conn)
    price_history: dict[str, list[float]] = {}

    print("Vetting strategies against real historical data before trading live...")
    approved_strategies = vet_strategies(conn)
    print(f"Approved for live trading: {[(s, strat.name) for s, strat, _, _ in approved_strategies]}")

    while True:
        run_cycle(conn, portfolio, broker, approved_strategies, price_history)
        time.sleep(POLL_SECONDS)


if __name__ == "__main__":
    main()
