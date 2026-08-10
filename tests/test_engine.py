import pandas as pd
import pytest
from src.backtest.engine import BacktestEngine


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