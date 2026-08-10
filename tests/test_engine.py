import pandas as pd
import numpy as np
import pytest
from src.backtest.engine import BacktestEngine, RiskBacktestEngine


def test_backtest_returns_nav_series():
    dates = pd.bdate_range("2020-01-01", periods=3)
    close = pd.Series([100.0, 110.0, 121.0], index=dates)
    px = pd.DataFrame({"close": close}, index=dates)
    engine = BacktestEngine(initial_cash=1_000_000)
    nav = engine.run(px, weights={"600000": 1.0})
    assert isinstance(nav, pd.Series)
    assert len(nav) == 3
    assert nav.iloc[0] == pytest.approx(1_000_000)
    assert nav.iloc[-1] == pytest.approx(1_000_000 * 1.1 * 1.1)


def test_backtest_empty_weights_flat_nav():
    dates = pd.bdate_range("2020-01-01", periods=5)
    close = pd.Series([100.0, 110.0, 121.0, 133.1, 146.41], index=dates)
    px = pd.DataFrame({"close": close}, index=dates)
    engine = BacktestEngine(initial_cash=1_000_000)
    nav = engine.run(px, weights={})
    assert (nav == 1_000_000).all()


def _prices(closes: dict[str, list[float]]) -> dict[str, pd.DataFrame]:
    n = len(next(iter(closes.values())))
    dates = pd.bdate_range("2020-01-01", periods=n)
    return {code: pd.DataFrame({"close": close}, index=dates)
            for code, close in closes.items()}


def test_risk_engine_buy_and_hold():
    # 缓涨序列，不触发止损/止盈/移动止损，真正验证持有
    prices = _prices({"600000": [100.0, 101.0, 102.0]})
    engine = RiskBacktestEngine(initial_cash=1_000_000)
    nav = engine.run(prices, {"600000": 1.0})
    assert nav.iloc[0] == pytest.approx(1_000_000)
    assert nav.iloc[-1] == pytest.approx(1_000_000 * 1.02)


def test_risk_engine_stop_loss():
    prices = _prices({"600000": [100.0, 91.0, 90.0]})
    engine = RiskBacktestEngine(initial_cash=1_000_000, stop_loss_pct=0.08)
    nav = engine.run(prices, {"600000": 1.0})
    # day2 回撤 9% >= 8% → 以 91 卖出，之后纯现金
    assert nav.iloc[-1] == pytest.approx(1_000_000 * 0.91)


def test_risk_engine_take_profit():
    prices = _prices({"600000": [100.0, 121.0, 122.0]})
    engine = RiskBacktestEngine(initial_cash=1_000_000, take_profit_pct=0.20)
    nav = engine.run(prices, {"600000": 1.0})
    # day2 涨幅 21% >= 20% → 以 121 止盈，之后纯现金
    assert nav.iloc[-1] == pytest.approx(1_000_000 * 1.21)


def test_risk_engine_empty_weights_flat():
    prices = _prices({"600000": [100.0, 110.0, 121.0]})
    engine = RiskBacktestEngine(initial_cash=1_000_000)
    nav = engine.run(prices, {})
    assert (nav == 1_000_000).all()