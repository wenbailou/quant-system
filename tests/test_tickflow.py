import pandas as pd
from src.data.tickflow import TickFlowDataLoader, _to_tickflow_code


class FakeKlines:
    def get(self, symbol, period="1d", count=100, as_dataframe=True, **kw):
        idx = pd.to_datetime(["2020-01-02", "2020-01-03"])
        return pd.DataFrame({
            "symbol": [symbol] * 2,
            "name": ["测试"] * 2,
            "trade_date": ["2020-01-02", "2020-01-03"],
            "open": [10.0, 10.2],
            "high": [10.5, 10.6],
            "low": [9.9, 10.0],
            "close": [10.1, 10.3],
            "volume": [1000, 2000],
            "amount": [10100.0, 20600.0],
        })


class FakeInstruments:
    def get(self, symbol):
        return {
            "symbol": symbol, "name": "测试", "type": "stock",
            "ext": {
                "listing_date": "2015-01-01",
                "float_shares": 1_000_000_000.0,
                "limit_up": 11.0, "limit_down": 9.0,
            },
        }


class FakeTF:
    def __init__(self):
        self.klines = FakeKlines()
        self.instruments = FakeInstruments()


def test_to_tickflow_code_maps_suffix():
    assert _to_tickflow_code("600000.XSHG") == "600000.SH"
    assert _to_tickflow_code("000001.XSHE") == "000001.SZ"
    assert _to_tickflow_code("000300.XSHG") == "000300.SH"
    assert _to_tickflow_code("600000.SH") == "600000.SH"


def test_load_stock_returns_ohlcv():
    tf = FakeTF()
    loader = TickFlowDataLoader("2020-01-01", "2020-01-10", tf=tf)
    df = loader.load_stock("600000.XSHG")
    assert {"open", "high", "low", "close", "volume", "amount"} <= set(df.columns)
    assert df.index[0] == pd.Timestamp("2020-01-02")


def test_load_index_returns_close():
    tf = FakeTF()
    loader = TickFlowDataLoader("2020-01-01", "2020-01-10", tf=tf)
    idx = loader.load_index("000300.XSHG")
    assert "close" in idx.columns
    assert len(idx) == 2


def test_load_stock_metadata():
    tf = FakeTF()
    loader = TickFlowDataLoader("2020-01-01", "2020-01-10", tf=tf)
    meta = loader.load_stock_metadata("600000.XSHG")
    assert meta["market_cap"] == 1_000_000_000.0 * 10.3  # float_shares × close
    assert meta["list_date"] == "2015-01-01"
    assert meta["is_st"] is False
    assert meta["limit_up"] == 11.0
    assert meta["limit_down"] == 9.0