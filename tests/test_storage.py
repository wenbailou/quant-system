import pandas as pd
from src.data.storage import MarketStore


def test_save_and_load_roundtrip(tmp_path):
    store = MarketStore(str(tmp_path / "test.db"))
    df = pd.DataFrame({
        "code": ["600000"] * 3,
        "date": pd.to_datetime(["2020-01-02", "2020-01-03", "2020-01-06"]),
        "close": [10.0, 10.5, 11.0],
    })
    store.save(df)
    loaded = store.load("600000")
    assert loaded["close"].tolist() == [10.0, 10.5, 11.0]