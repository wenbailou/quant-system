import pandas as pd
from src.features.indicators import add_sma, add_returns, add_rsi


def build_features(df: pd.DataFrame) -> pd.DataFrame:
    out = df.copy()
    out = add_sma(out, 5)
    out = add_sma(out, 20)
    out = add_returns(out, 1)
    out = add_returns(out, 5)
    out = add_rsi(out, 14)
    return out


FEATURE_COLUMNS = ["sma_5", "sma_20", "ret_1", "ret_5", "rsi_14"]


def prepare_feature_matrix(df: pd.DataFrame) -> tuple[pd.DataFrame, list[str]]:
    out = build_features(df)
    X = out[FEATURE_COLUMNS].dropna()
    return X, FEATURE_COLUMNS