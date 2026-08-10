import pandas as pd


def chronological_split(
    df: pd.DataFrame,
    val_ratio: float = 0.2,
    test_ratio: float = 0.2,
) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    """按时间顺序切分，保证无未来数据泄漏。"""
    assert val_ratio + test_ratio < 1.0
    df = df.sort_values("date").reset_index(drop=True)
    n = len(df)
    test_n = int(n * test_ratio)
    val_n = int(n * val_ratio)
    train = df.iloc[: n - val_n - test_n]
    val = df.iloc[n - val_n - test_n: n - test_n]
    test = df.iloc[n - test_n:]
    return train, val, test