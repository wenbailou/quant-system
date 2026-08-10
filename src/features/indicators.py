import pandas as pd
import numpy as np


def add_sma(df: pd.DataFrame, window: int) -> pd.DataFrame:
    df = df.copy()
    df[f"sma_{window}"] = df["close"].rolling(window).mean()
    return df


def add_returns(df: pd.DataFrame, window: int) -> pd.DataFrame:
    df = df.copy()
    df[f"ret_{window}"] = df["close"].pct_change(periods=window)
    return df


def add_rsi(df: pd.DataFrame, window: int = 14) -> pd.DataFrame:
    df = df.copy()
    delta = df["close"].diff()
    gain = delta.clip(lower=0)
    loss = -delta.clip(upper=0)
    avg_gain = gain.ewm(alpha=1 / window, min_periods=window).mean()
    avg_loss = loss.ewm(alpha=1 / window, min_periods=window).mean()
    rs = avg_gain / avg_loss.replace(0, np.nan)
    df["rsi_14"] = 100 - (100 / (1 + rs))
    return df