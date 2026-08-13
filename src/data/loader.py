import pandas as pd
import numpy as np
from src.data.base import MarketDataLoader


class MockMarketDataLoader(MarketDataLoader):
    """模拟行情源，用于开发与测试。"""

    def __init__(self, start: str, end: str, seed: int = 42):
        self.start = pd.Timestamp(start)
        self.end = pd.Timestamp(end)
        self._rng = np.random.default_rng(seed)

    def _date_range(self) -> pd.DatetimeIndex:
        return pd.bdate_range(self.start, self.end)

    def load_stock(self, code: str) -> pd.DataFrame:
        idx = self._date_range()
        n = len(idx)
        close = 10 * np.cumprod(1 + self._rng.normal(0, 0.02, n))
        high = close * (1 + np.abs(self._rng.normal(0, 0.01, n)))
        low = close * (1 - np.abs(self._rng.normal(0, 0.01, n)))
        open_ = np.concatenate([[close[0]], close[:-1]])
        volume = self._rng.integers(1_000_000, 10_000_000, n)
        amount = volume * close
        return pd.DataFrame(
            {"open": open_, "high": high, "low": low, "close": close,
             "volume": volume, "amount": amount},
            index=idx,
        )

    def load_index(self, code: str) -> pd.DataFrame:
        return self.load_stock(code)

    def load_stock_metadata(self, code: str) -> dict:
        """生成确定的模拟元数据（市值/上市日期/ST/行业）。

        基于股票代码哈希做确定性种子，保证同一 code 每次结果一致，
        且不同 code 呈现不同的市值/ST/行业特征，便于演示准入过滤。
        """
        seed = abs(hash(code)) % 1000
        rng = np.random.default_rng(seed)
        # 流通市值：10亿 ~ 3000亿，部分微盘（<30亿）用于演示市值过滤
        market_cap = float(rng.uniform(1e9, 3e11))
        # 上市日期：2010-2024 之间随机，部分次新
        list_year = int(rng.uniform(2010, 2025))
        list_date = f"{list_year}-{int(rng.uniform(1, 13)):02d}-{int(rng.uniform(1, 29)):02d}"
        # 约 15% 概率为 ST
        is_st = bool(rng.random() < 0.15)
        industries = ["银行", "医药", "消费", "科技", "制造", "地产"]
        industry = industries[int(rng.integers(0, len(industries)))]
        # 主板默认 10% 涨跌停
        limit_pct = 0.10
        return {
            "market_cap": market_cap,
            "list_date": list_date,
            "is_st": is_st,
            "industry": industry,
            "limit_pct": limit_pct,
        }