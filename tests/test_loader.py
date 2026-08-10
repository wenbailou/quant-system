import pandas as pd
from src.data.loader import MockMarketDataLoader


def test_loader_returns_ohlcv_columns():
    loader = MockMarketDataLoader(start="2020-01-01", end="2020-01-10")
    df = loader.load_stock("600000")
    expected_cols = {"open", "high", "low", "close", "volume", "amount"}
    assert expected_cols.issubset(set(df.columns))


def test_loader_returns_index_data():
    loader = MockMarketDataLoader(start="2020-01-01", end="2020-01-10")
    idx = loader.load_index("000300")
    assert not idx.empty
    assert "close" in idx.columns