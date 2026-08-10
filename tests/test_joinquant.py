import pandas as pd
import pytest
from src.data.joinquant import JoinQuantDataLoader


class FakeJQ:
    """伪造的 jqdatasdk，避免在无凭证环境下实际调用聚宽接口。"""

    def __init__(self):
        self.auth_called = False

    def auth(self, account, password):
        self.auth_called = True

    def get_price(self, code, start_date, end_date, frequency, fields, fq):
        idx = pd.to_datetime(["2020-01-02", "2020-01-03"])
        return pd.DataFrame({
            "open": [10.0, 10.2],
            "close": [10.1, 10.3],
            "high": [10.5, 10.6],
            "low": [9.9, 10.0],
            "volume": [1000, 2000],
            "money": [10100.0, 20600.0],
        }, index=idx)


def test_joinquant_load_stock_maps_columns():
    jq = FakeJQ()
    loader = JoinQuantDataLoader("2020-01-01", "2020-01-10", "acc", "pwd",
                                 jq=jq)
    df = loader.load_stock("600000.XSHG")
    assert jq.auth_called
    assert {"open", "high", "low", "close", "volume", "amount"} <= set(df.columns)
    assert "money" not in df.columns
    assert df["amount"].tolist() == [10100.0, 20600.0]


def test_joinquant_missing_credentials_raises():
    jq = FakeJQ()
    loader = JoinQuantDataLoader("2020-01-01", "2020-01-10", "", "", jq=jq)
    with pytest.raises(RuntimeError):
        loader.load_stock("600000.XSHG")
    assert not jq.auth_called