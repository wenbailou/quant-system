import pandas as pd
import numpy as np
import pytest
from src.features.indicators import add_sma, add_returns, add_rsi


def test_add_sma():
    df = pd.DataFrame({"close": [1, 2, 3, 4, 5]})
    df = add_sma(df, window=3)
    assert df["sma_3"].iloc[2] == 2.0
    assert pd.isna(df["sma_3"].iloc[0])


def test_add_returns():
    df = pd.DataFrame({"close": [10.0, 10.5, 10.0]})
    df = add_returns(df, window=1)
    assert df["ret_1"].iloc[1] == pytest.approx(0.05)


def test_add_rsi_value_range():
    df = pd.DataFrame({"close": np.linspace(10, 20, 30)})
    df = add_rsi(df, window=14)
    rsi = df["rsi_14"].dropna()
    assert ((rsi >= 0) & (rsi <= 100)).all()