import pandas as pd

from src.strategy.eligibility import (
    avg_amount,
    is_suspended,
    is_limit_up,
    list_trading_days,
    parse_rejected,
    screen_stocks,
)


def _stock(amount=100_000_000, volume=1_000_000, n=80, close=10.0):
    idx = pd.bdate_range("2020-01-01", periods=n)
    return pd.DataFrame({
        "open": [close] * n, "high": [close] * n, "low": [close] * n,
        "close": [close] * n, "volume": [volume] * n, "amount": [amount] * n,
    }, index=idx)


def _cfg():
    return {
        "risk": {
            "min_avg_amount": 50_000_000,
            "min_list_days": 60,
            "min_market_cap": 3_000_000_000,
        },
    }


def test_avg_amount():
    df = _stock(amount=100_000_000)
    assert avg_amount(df) == 100_000_000
    assert avg_amount(df, window=5) == 100_000_000


def test_is_suspended():
    assert is_suspended(_stock(volume=0)) is True
    assert is_suspended(_stock(volume=1_000_000)) is False


def test_is_limit_up():
    df = _stock()
    df["pre_close"] = df["close"]
    df.loc[df.index[-1], "close"] = 11.0  # +10% → 涨停
    assert is_limit_up(df, limit_pct=0.10) is True


def test_list_trading_days():
    assert list_trading_days(_stock(n=80)) == 80


def test_screen_filters_illiquid_zero_amount():
    stocks = {"A": _stock(amount=100_000_000), "B": _stock(amount=1_000_000)}
    eligible, rejected = screen_stocks(stocks, _cfg())
    assert "A" in eligible
    assert "B" not in eligible
    assert any("流动性" in r for r in rejected["B"])


def test_screen_filters_low_list_days():
    stocks = {"A": _stock(n=80), "B": _stock(n=30)}
    eligible, rejected = screen_stocks(stocks, _cfg())
    assert "A" in eligible
    assert "B" not in eligible
    assert any("上市" in r for r in rejected["B"])


def test_screen_filters_small_market_cap():
    stocks = {"A": _stock(), "B": _stock()}
    meta = {"A": {"market_cap": 100_000_000_000},  # 1000亿
            "B": {"market_cap": 1_000_000_000}}    # 10亿
    eligible, rejected = screen_stocks(stocks, _cfg(), metadata=meta)
    assert "A" in eligible
    assert "B" not in eligible
    assert any("市值" in r for r in rejected["B"])


def test_screen_filters_st_and_suspended():
    stocks = {"A": _stock(), "B": _stock(), "C": _stock(volume=0)}
    meta = {"A": {"is_st": False}, "B": {"is_st": True}}
    eligible, rejected = screen_stocks(stocks, _cfg(), metadata=meta)
    assert "A" in eligible
    assert "B" not in eligible and any("ST" in r for r in rejected["B"])
    assert "C" not in eligible and any("停牌" in r for r in rejected["C"])


def test_screen_filters_limit_up():
    stocks = {"A": _stock(), "B": _stock()}
    # 先记录前收盘（10.0），再令 B 末日涨至 11.0（+10% 涨停）
    stocks["A"]["pre_close"] = stocks["A"]["close"]
    stocks["B"]["pre_close"] = stocks["B"]["close"]
    stocks["B"].loc[stocks["B"].index[-1], "close"] = 11.0
    eligible, rejected = screen_stocks(stocks, _cfg())
    assert "A" in eligible
    assert "B" not in eligible and any("涨停" in r for r in rejected["B"])


def test_parse_rejected_returns_reasons():
    stocks = {"A": _stock(amount=1_000_000)}
    _, rejected = screen_stocks(stocks, _cfg())
    reasons = parse_rejected(rejected)
    assert "A" in reasons
    assert isinstance(reasons["A"], list) and reasons["A"]