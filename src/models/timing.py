import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestClassifier
from src.features.pipeline import FEATURE_COLUMNS, build_features


class TimingModel:
    """预测未来 N 日指数方向，映射为仓位档位。"""

    def __init__(self, predict_horizon: int = 5):
        self.predict_horizon = predict_horizon
        self.model = RandomForestClassifier(n_estimators=100, random_state=42)

    def _make_label(self, df: pd.DataFrame) -> pd.Series:
        future = df["close"].shift(-self.predict_horizon)
        ret = (future - df["close"]) / df["close"]
        return (ret > 0).astype(int)

    def fit(self, df: pd.DataFrame):
        feats = build_features(df)
        X = feats[FEATURE_COLUMNS]
        y = self._make_label(feats)
        mask = X.notna().all(axis=1) & y.notna()
        self.model.fit(X[mask], y[mask].astype(int))
        return self

    def predict_proba_up(self, df: pd.DataFrame) -> float:
        feats = build_features(df)
        X = feats[FEATURE_COLUMNS].dropna()
        if X.empty:
            return 0.5
        return float(self.model.predict_proba(X)[-1][1])

    def predict_position(self, df: pd.DataFrame, position_levels: dict) -> float:
        p = self.predict_proba_up(df)
        if p >= 0.7:
            return position_levels["bull"]
        if p >= 0.6:
            return position_levels["neutral"]
        if p >= 0.4:
            return position_levels["bear"]
        return position_levels["strong_bear"]