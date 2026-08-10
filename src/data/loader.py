import pandas as pd
import numpy as np


class MockMarketDataLoader:
    """模拟行情源，真实实现需替换为聚宽/优矿/通联接口。"""

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