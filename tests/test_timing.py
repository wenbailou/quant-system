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