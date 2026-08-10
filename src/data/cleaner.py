import pandas as pd


def mark_limit(df: pd.DataFrame, limit_pct: float = 0.10) -> pd.Series:
    """标记涨停（主板默认 10%）。"""
    change = (df["close"] - df["pre_close"]) / df["pre_close"]
    return change >= limit_pct - 1e-6


def filter_st(df: pd.DataFrame, st_codes: set[str]) -> pd.DataFrame:
    return df[~df["code"].isin(st_codes)]


def drop_suspended(df: pd.DataFrame, suspended_days: set[str]) -> pd.DataFrame:
    return df[~df["date"].isin(suspended_days)]