import numpy as np
import pandas as pd
import pytest
from src.backtest.metrics import annualized_return, max_drawdown, sharpe_ratio


def test_annualized_return():
    nav = pd.Series([1.0, 1.1, 1.21])
    assert annualized_return(nav) == pytest.approx(0.10, rel=0.05)


def test_max_drawdown():
    nav = pd.Series([1.0, 1.5, 1.2, 1.3])
    assert max_drawdown(nav) == pytest.approx(0.20, rel=0.05)


def test_sharpe_ratio():
    nav = pd.Series(np.linspace(1.0, 1.5, 100))
    assert sharpe_ratio(nav) >= 0