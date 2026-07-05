from tradingbot.strategies.momentum import MomentumStrategy
from tradingbot.backtest.runner import run_backtest


def test_backtest_uptrend_strategy_passes():
    strat = MomentumStrategy(lookback=5, threshold=0.0)
    # steady uptrend: momentum strategy should catch it and profit
    closes = [100 + i for i in range(60)]
    result = run_backtest(strat, closes)
    assert result.strategy == "momentum"
    assert result.num_trades >= 2
    assert result.total_pnl > 0
    assert result.passed is True
    assert result.reason == "passed"


def test_backtest_flat_market_fails():
    strat = MomentumStrategy(lookback=5, threshold=0.0)
    closes = [100.0] * 60
    result = run_backtest(strat, closes)
    assert result.num_trades == 0
    assert result.passed is False
    assert "no trades" in result.reason.lower()


def test_backtest_result_has_drawdown_and_sharpe_fields():
    strat = MomentumStrategy(lookback=5, threshold=0.0)
    closes = [100 + i for i in range(60)]
    result = run_backtest(strat, closes)
    assert isinstance(result.sharpe, float)
    assert isinstance(result.max_drawdown, float)
