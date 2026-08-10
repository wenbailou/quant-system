import pandas as pd
import pytest
from src.models.split import chronological_split


def test_chronological_split_no_leakage():
    dates = pd.to_datetime(["2020-01-02", "2020-01-03", "2020-01-06",
                            "2020-01-07", "2020-01-08", "2020-01-09"])
    df = pd.DataFrame({"date": dates, "value": range(6)})
    train, val, test = chronological_split(df, val_ratio=0.33, test_ratio=0.33)
    assert set(train["date"]).isdisjoint(set(val["date"]))
    assert set(train["date"]).isdisjoint(set(test["date"]))
    assert train["date"].max() < val["date"].min()
    assert val["date"].max() < test["date"].min()
    assert len(train) + len(val) + len(test) == len(df)


def test_split_raises_when_ratios_sum_to_one():
    df = pd.DataFrame({"date": pd.to_datetime(range(10)), "value": range(10)})
    with pytest.raises(ValueError):
        chronological_split(df, val_ratio=0.5, test_ratio=0.5)


def test_split_raises_on_negative_ratio():
    df = pd.DataFrame({"date": pd.to_datetime(range(10)), "value": range(10)})
    with pytest.raises(ValueError):
        chronological_split(df, val_ratio=-0.1, test_ratio=0.2)