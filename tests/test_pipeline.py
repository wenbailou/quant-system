import pandas as pd
from src.features.pipeline import build_features


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