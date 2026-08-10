import pandas as pd


def chronological_split(
    df: pd.DataFrame,
    val_ratio: float = 0.2,
    test_ratio: float = 0.2,
) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    """按时间顺序切分，保证无未来数据泄漏。"""
    if not 0.0 <= val_ratio < 1.0 or not 0.0 <= test_ratio < 1.0:
        raise ValueError("val_ratio 和 test_ratio 必须在 [0, 1) 区间")
    if val_ratio + test_ratio >= 1.0:
        raise ValueError("val_ratio + test_ratio 必须小于 1.0")
    df = df.sort_values("date").reset_index(drop=True)
    n = len(df)
    test_n = int(n * test_ratio)
    val_n = int(n * val_ratio)
    train = df.iloc[: n - val_n - test_n]
    val = df.iloc[n - val_n - test_n: n - test_n]
    test = df.iloc[n - test_n:]
    return train, val, test