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


def test_loader_returns_metadata_fields():
    loader = MockMarketDataLoader(start="2020-01-01", end="2020-01-10")
    meta = loader.load_stock_metadata("600000.XSHG")
    assert "market_cap" in meta
    assert "list_date" in meta
    assert "is_st" in meta
    assert isinstance(meta["market_cap"], float)
    assert isinstance(meta["is_st"], bool)


def test_loader_metadata_deterministic():
    loader = MockMarketDataLoader(start="2020-01-01", end="2020-01-10")
    m1 = loader.load_stock_metadata("600000.XSHG")
    m2 = loader.load_stock_metadata("600000.XSHG")
    assert m1 == m2