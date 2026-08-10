from abc import ABC, abstractmethod
import pandas as pd


class MarketDataLoader(ABC):
    """行情数据源统一接口。

    真实数据源（聚宽、优矿、通联等）通过实现本接口接入系统，
    上层（特征/模型/看板）只依赖本接口，不感知具体数据源。
    """

    @abstractmethod
    def load_stock(self, code: str) -> pd.DataFrame:
        """加载单只股票的日线 OHLCV 数据。

        返回 DataFrame，含 open/high/low/close/volume/amount 六列，
        以交易日为索引。
        """

    @abstractmethod
    def load_index(self, code: str) -> pd.DataFrame:
        """加载指数日线数据，列结构同 load_stock。"""