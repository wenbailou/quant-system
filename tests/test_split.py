import pandas as pd
from src.models.split import chronological_split


def test_chronological_split_no_leakage():
    dates = pd.to_datetime(["2020-01-02", "2020-01-03", "2020-01-06",
                            "2020-01-07", "2020-01-08", "2020-01-09"])
    df = pd.DataFrame({"date": dates, "value": range(6)})
    train, val, test = chronological_split(df, val_ratio=0.33, test_ratio=0.33)
    assert set(train["date"]).isdisjoint(set(val["date"]))
    assert set(train["date"]).isdisjoint(set(test["date"]))
    assert test["value"].max() > 0