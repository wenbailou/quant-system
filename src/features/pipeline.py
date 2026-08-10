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
    """构建特征矩阵 X。

    对输入 df 构造特征后将含 NaN 的行整体删除（dropna），因此返回的 X 的
    index 是原始 df.index 的非连续子集，且 len(X) < len(df)。

    调用方必须用「与 X 相同 index 的标签」进行对齐，例如：

        X, cols = prepare_feature_matrix(df)
        y = df.loc[X.index, "target"]

    或先对 X 调用 reset_index(drop=True) 后按位置对齐。禁止用全量长度的标签
    做位置切片（例如 y = df["target"] 再按前 len(X) 切片），否则会造成标签错配。
    """
    out = build_features(df)
    X = out[FEATURE_COLUMNS].dropna()
    return X, FEATURE_COLUMNS