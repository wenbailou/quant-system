import numpy as np
import pandas as pd
from src.features.pipeline import FEATURE_COLUMNS, build_features


class SelectionModel:
    """按滚动末段收益动量对个股排序，取 Top-K。"""

    def __init__(self, top_k: int = 10):
        self.top_k = top_k

    def fit(self, stocks: dict[str, pd.DataFrame]):
        # 简化：此处省略训练，直接基于动量排序
        return self

    def score_stock(self, df: pd.DataFrame) -> float:
        feats = build_features(df)
        ret = feats["ret_5"].dropna()
        return float(ret.iloc[-1]) if not ret.empty else 0.0

    def select(self, stocks: dict[str, pd.DataFrame]) -> list[str]:
        scores = {code: self.score_stock(df) for code, df in stocks.items()}
        ranked = sorted(scores, key=scores.get, reverse=True)
        return ranked[: self.top_k]