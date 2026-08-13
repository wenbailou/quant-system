import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestRegressor
from joblib import dump, load

from src.features.pipeline import FEATURE_COLUMNS, build_features

# 训练数据最小样本量；不足时退化为动量排序
MIN_TRAIN_SAMPLES = 30


class SelectionModel:
    """监督学习选股模型：预测未来 N 日收益并据此对个股排序取 Top-K。

    训练：从样本期个股面板数据构造「特征 → 未来收益」训练集，
    用随机森林回归学习历史特征与未来收益的关系。
    预测：对每只股票的最新特征预测其未来收益期望，按分数降序取 Top-K。

    当样本量不足时退化为动量排序（ret_5 最大者优先），保证在
    冷启动/短样本场景下仍可用。
    """

    def __init__(self, top_k: int = 10, label_horizon: int = 5):
        self.top_k = top_k
        self.label_horizon = label_horizon
        self._model = None
        self._trained = False

    def _build_training_data(
        self,
        stocks: dict[str, pd.DataFrame],
        label_horizon: int,
    ) -> tuple[pd.DataFrame, pd.Series]:
        """构造面板训练数据。

        对每只股票构造特征，并以「未来 label_horizon 日收益」为标签，
        仅保留标签非空的样本（剔除序列末尾无法计算未来收益的行）。
        返回 (X, y)，且 X 与 y 按位置对齐。
        """
        X_list: list[pd.DataFrame] = []
        y_list: list[pd.Series] = []

        for code, df in stocks.items():
            feats = build_features(df)
            close = df["close"]
            # 未来 label_horizon 日收益 = close.shift(-label_horizon) / close - 1
            forward = close.shift(-label_horizon) / close - 1
            X = feats[FEATURE_COLUMNS].copy()
            y = forward
            # 对齐：仅保留特征与标签均非 NaN 的行
            mask = X.notna().all(axis=1) & y.notna()
            X = X[mask]
            y = y[mask]
            if len(X) > 0:
                X_list.append(X)
                y_list.append(y)

        if not X_list:
            return pd.DataFrame(), pd.Series(dtype=float)

        X_all = pd.concat(X_list, axis=0)
        y_all = pd.concat(y_list, axis=0)
        return X_all, y_all

    def fit(self, stocks: dict[str, pd.DataFrame]):
        """用样本期个股面板数据训练随机森林回归模型。"""
        X, y = self._build_training_data(stocks, self.label_horizon)
        if len(X) >= MIN_TRAIN_SAMPLES:
            model = RandomForestRegressor(
                n_estimators=100, max_depth=6, random_state=42, n_jobs=-1,
            )
            model.fit(X, y)
            self._model = model
            self._trained = True
        else:
            # 样本不足：退化为动量排序（不训练模型）
            self._model = None
            self._trained = False
        return self

    def score_stock(self, df: pd.DataFrame) -> float:
        """预测单只股票的未来收益期望（最新特征）。"""
        feats = build_features(df)
        if self._trained and self._model is not None:
            latest = feats[FEATURE_COLUMNS].iloc[-1:]
            latest = latest.dropna()
            if len(latest) == 1:
                pred = self._model.predict(latest)[0]
                if np.isfinite(pred):
                    return float(pred)
        # 模型不可用或特征缺失 → 退回动量分数
        ret = feats["ret_5"].dropna()
        return float(ret.iloc[-1]) if not ret.empty else 0.0

    def select(self, stocks: dict[str, pd.DataFrame]) -> list[str]:
        scores = {code: self.score_stock(df) for code, df in stocks.items()}
        ranked = sorted(scores, key=scores.get, reverse=True)
        return ranked[: self.top_k]

    def save(self, path: str) -> None:
        """持久化模型配置与已训练模型到磁盘（joblib）。"""
        dump({"model": self._model, "trained": self._trained,
              "top_k": self.top_k, "label_horizon": self.label_horizon},
             path)

    @classmethod
    def load(cls, path: str) -> "SelectionModel":
        """从磁盘加载模型。"""
        data = load(path)
        obj = cls(top_k=data.get("top_k", 10),
                  label_horizon=data.get("label_horizon", 5))
        obj._model = data.get("model")
        obj._trained = bool(data.get("trained", False))
        return obj