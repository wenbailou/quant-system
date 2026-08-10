import pandas as pd
from src.features.pipeline import build_features, prepare_feature_matrix


def test_prepare_feature_matrix_index_contract():
    df = pd.DataFrame({
        "close": [10 + i for i in range(30)],
        "high": [11 + i for i in range(30)],
        "low": [9 + i for i in range(30)],
        "open": [10 + i for i in range(30)],
        "volume": [1000] * 30,
        "amount": [10000] * 30,
    })
    X, cols = prepare_feature_matrix(df)
    assert X.index.isin(df.index).all()
    assert len(X) < len(df)
    assert X.isna().sum().sum() == 0
    y = df.loc[X.index, "close"]
    assert len(y) == len(X)


def test_build_features_columns():
    df = pd.DataFrame({
        "close": [10 + i for i in range(20)],
        "volume": [1000] * 20,
        "amount": [10000] * 20,
        "high": [10 + i + 1 for i in range(20)],
        "low": [10 + i - 1 for i in range(20)],
        "open": [10 + i for i in range(20)],
    })
    out = build_features(df)
    assert {"sma_5", "sma_20", "ret_1", "ret_5", "rsi_14"}.issubset(set(out.columns))