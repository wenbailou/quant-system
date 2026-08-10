import pandas as pd
from src.data.cleaner import mark_limit, filter_st, drop_suspended


def test_mark_limit():
    df = pd.DataFrame({
        "close": [10.0, 11.0, 9.9],
        "pre_close": [10.0, 10.0, 10.0],
    })
    df["limit_up"] = mark_limit(df)
    assert df["limit_up"].tolist() == [False, True, False]


def test_filter_st():
    df = pd.DataFrame({"code": ["600001", "600002", "600003"]})
    st_codes = {"600002"}
    result = filter_st(df, st_codes)
    assert result["code"].tolist() == ["600001", "600003"]


def test_drop_suspended():
    df = pd.DataFrame({"date": ["2020-01-02", "2020-01-03", "2020-01-06"]})
    suspended_days = {"2020-01-03"}
    result = drop_suspended(df, suspended_days)
    assert result["date"].tolist() == ["2020-01-02", "2020-01-06"]