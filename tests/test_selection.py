import pandas as pd
import numpy as np
from src.models.selection import SelectionModel


def test_selection_top_k():
    stocks = {}
    for code in ["600001", "600002", "600003", "600004"]:
        dates = pd.bdate_range("2020-01-01", periods=60)
        drift = {"600001": 0.01, "600002": 0.02, "600003": 0.0, "600004": -0.01}[code]
        close = 100 * np.cumprod(1 + drift + np.random.normal(0, 0.01, len(dates)))
        stocks[code] = pd.DataFrame({"date": dates, "close": close})
    model = SelectionModel(top_k=2)
    model.fit(stocks)
    picks = model.select(stocks)
    assert len(picks) == 2
    assert all(c in stocks for c in picks)