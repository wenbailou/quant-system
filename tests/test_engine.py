import pandas as pd
import numpy as np
from src.backtest.engine import BacktestEngine


def test_backtest_returns_nav_series():
    dates = pd.bdate_range("2020-01-01", periods=60)
    close = 100 * np.cumprod(1 + np.random.normal(0, 0.01, len(dates)))
    px = pd.DataFrame({"close": close}, index=dates)
    engine = BacktestEngine(initial_cash=1_000_000)
    nav = engine.run(px, weights={"600000": 1.0})
    assert isinstance(nav, pd.Series)
    assert len(nav) == len(dates)
    assert nav.iloc[-1] > 0