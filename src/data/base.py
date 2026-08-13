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

    @abstractmethod
    def load_stock_metadata(self, code: str) -> dict:
        """加载单只股票的静态元数据（用于准入过滤）。

        返回字典，至少应包含：
        - market_cap: 最新流通市值（元）
        - list_date: 上市日期（str, YYYY-MM-DD）
        - is_st: 是否 ST/*ST（bool）
        可选：
        - industry: 所属行业板块（str）
        - limit_pct: 涨跌停幅度（如 0.10 / 0.05 / 0.20）
        """
        raise NotImplementedError