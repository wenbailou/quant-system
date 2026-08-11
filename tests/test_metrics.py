import numpy as np
import pandas as pd
import pytest
from src.backtest.metrics import (
    annualized_return, max_drawdown, sharpe_ratio,
    win_rate, profit_factor, turnover_rate, excess_return,
)


def test_annualized_return():
    nav = pd.Series([1.0, 1.1])
    assert annualized_return(nav, periods_per_year=1) == pytest.approx(0.10, rel=0.05)


def test_max_drawdown():
    nav = pd.Series([1.0, 1.5, 1.2, 1.3])
    assert max_drawdown(nav) == pytest.approx(0.20, rel=0.05)


def test_sharpe_ratio():
    nav = pd.Series(np.linspace(1.0, 1.5, 100))
    assert sharpe_ratio(nav) >= 0


def test_win_rate():
    nav = pd.Series([1.0, 1.1, 1.05, 1.2])
    # 三日收益：+10%, -4.5%, +14% → 2 正 1 负 → 胜率 2/3
    assert win_rate(nav) == pytest.approx(2 / 3)


def test_win_rate_no_gains():
    # 收益 -10%, +5.6% → 1 正 1 负 → 胜率 0.5
    nav = pd.Series([1.0, 0.9, 0.95])
    assert win_rate(nav) == pytest.approx(0.5)


def test_profit_factor():
    nav = pd.Series([1.0, 1.2, 0.9, 1.1])
    # 收益: +0.2, -0.25, +0.22 → 盈利 0.2+0.22=0.42, 亏损 0.25 → 1.68
    assert profit_factor(nav) == pytest.approx(0.42 / 0.25, rel=0.05)


def test_profit_factor_no_loss():
    nav = pd.Series([1.0, 1.1, 1.2])
    assert profit_factor(nav) == float("inf")


def test_turnover_rate():
    w1 = np.array([0.5, 0.5])
    w2 = np.array([0.3, 0.7])
    # 单次调仓换手 = (|0.5-0.3|+|0.5-0.7|) = 0.4
    assert turnover_rate(w1, w2) == pytest.approx(0.4)


def test_excess_return():
    strat = pd.Series([1_000_000, 1_100_000])
    bench = pd.Series([1_000_000, 1_000_000])
    # 策略 +10%，基准 0% → 超额 10%
    assert excess_return(strat, bench) == pytest.approx(0.10, rel=0.05)