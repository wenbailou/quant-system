import pandas as pd
import numpy as np
from src.models.timing import TimingModel


def test_timing_model_predicts_position():
    dates = pd.bdate_range("2020-01-01", periods=200)
    close = 100 * np.cumprod(1 + np.random.normal(0.001, 0.02, len(dates)))
    df = pd.DataFrame({"date": dates, "close": close})
    model = TimingModel(predict_horizon=5)
    model.fit(df)
    pos = model.predict_position(df, position_levels={
        "strong_bear": 0.0, "bear": 0.3, "neutral": 0.6, "bull": 0.9,
    })
    assert pos in (0.0, 0.3, 0.6, 0.9)


def test_make_label_nan_for_future_unknown():
    dates = pd.bdate_range("2020-01-01", periods=10)
    df = pd.DataFrame({"date": dates, "close": range(10, 20)})
    model = TimingModel(predict_horizon=5)
    label = model._make_label(df)
    assert label.iloc[-5:].isna().all()
    assert label.iloc[:5].notna().all()


def test_predict_position_threshold_mapping(monkeypatch):
    levels = {"strong_bear": 0.0, "bear": 0.3, "neutral": 0.6, "bull": 0.9}
    model = TimingModel(predict_horizon=5)
    df = pd.DataFrame({"date": pd.bdate_range("2020-01-01", periods=10),
                       "close": range(10, 20)})
    cases = [(0.8, 0.9), (0.7, 0.9), (0.65, 0.6), (0.5, 0.3), (0.4, 0.3), (0.2, 0.0)]
    for p, expected in cases:
        monkeypatch.setattr(model, "predict_proba_up", lambda df, p=p: p)
        assert model.predict_position(df, levels) == expected