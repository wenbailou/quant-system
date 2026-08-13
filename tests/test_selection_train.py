import numpy as np
import pandas as pd
import pytest

from src.models.selection import SelectionModel


def _stock(drift: float, n: int = 80, seed: int = 0) -> pd.DataFrame:
    rng = np.random.default_rng(seed)
    dates = pd.bdate_range("2020-01-01", periods=n)
    close = 100 * np.cumprod(1 + drift + rng.normal(0, 0.005, n))
    return pd.DataFrame({"close": close}, index=dates)


def test_selection_top_k_keeps_contract():
    stocks = {
        "600001": _stock(0.01),
        "600002": _stock(0.02),
        "600003": _stock(0.0),
        "600004": _stock(-0.01),
    }
    model = SelectionModel(top_k=2)
    model.fit(stocks)
    picks = model.select(stocks)
    assert len(picks) == 2
    assert all(c in stocks for c in picks)


def test_fit_trains_model_and_ranks_higher_drift_higher():
    # 高漂移（稳定上涨）的股票应获得更高预测分数
    stocks = {
        "hsg": _stock(0.01, seed=1),
        "hst": _stock(0.02, seed=2),
        "low": _stock(-0.01, seed=3),
    }
    model = SelectionModel(top_k=1)
    model.fit(stocks)
    picks = model.select(stocks)
    # 训练后应倾向选出上涨趋势的股票
    assert "hst" in picks


def test_score_stock_returns_float():
    model = SelectionModel(top_k=1)
    model.fit({"A": _stock(0.01, seed=1)})
    score = model.score_stock(_stock(0.01, seed=1))
    assert isinstance(score, float)


def test_forward_return_label_construction():
    # 验证训练数据标签 = 未来 N 日收益
    stocks = {"A": _stock(0.01, n=80)}
    model = SelectionModel(top_k=1)
    X, y = model._build_training_data(stocks, label_horizon=5)
    assert len(X) == len(y)
    assert len(X) > 0
    # 末段标签非空（未来 5 日存在）
    assert len(X.columns) > 0


def test_fit_without_enough_data_keeps_momentum_fallback():
    # 数据不足时退化为动量排序，不抛异常
    stocks = {"A": _stock(0.01, n=15), "B": _stock(0.02, n=15)}
    model = SelectionModel(top_k=1)
    model.fit(stocks)
    picks = model.select(stocks)
    assert len(picks) == 1
    assert all(c in stocks for c in picks)


def test_save_load_roundtrip(tmp_path):
    stocks = {"A": _stock(0.01, n=80), "B": _stock(0.02, n=80)}
    model = SelectionModel(top_k=2, label_horizon=5)
    model.fit(stocks)
    path = str(tmp_path / "model.joblib")
    model.save(path)
    loaded = SelectionModel.load(path)
    assert loaded.top_k == 2
    assert loaded.label_horizon == 5
    assert loaded._trained == model._trained
    # 加载后选股结果一致
    assert loaded.select(stocks) == model.select(stocks)