"""标的准入过滤（设计文档 5.3 节）。

在选股排序前对候选标的做准入门槛过滤，剔除：
- 涨跌停（无法成交）
- ST/*ST（退市与流动性风险）
- 停牌（无法成交）
- 流动性不足（近 20 日均成交额过低）
- 次新（上市交易日过短）
- 微盘股（市值过小）

其中流动性/次新/停牌/涨跌停可从行情数据派生；市值、ST 等个股
属性需由数据源通过 metadata 提供（mock 生成，真实源后续实现）。
"""
from __future__ import annotations

import pandas as pd


def avg_amount(df: pd.DataFrame, window: int = 20) -> float:
    """近 window 个交易日均成交额。"""
    return float(df["amount"].tail(window).mean())


def is_suspended(df: pd.DataFrame) -> bool:
    """最新交易日是否停牌（当日成交量 / 成交额为 0）。"""
    vol = df["volume"].iloc[-1]
    amt = df["amount"].iloc[-1]
    return bool(vol == 0 or amt == 0)


def is_limit_up(df: pd.DataFrame, limit_pct: float = 0.10) -> bool:
    """最新交易日是否涨停。需行情含 pre_close 列。"""
    if "pre_close" not in df.columns:
        return False
    close = df["close"].iloc[-1]
    pre = df["pre_close"].iloc[-1]
    if not pre:
        return False
    return bool((close - pre) / pre >= limit_pct - 1e-6)


def list_trading_days(df: pd.DataFrame) -> int:
    """以可用行情天数近似上市交易日数。"""
    return int(len(df))


def screen_stocks(
    stocks: dict[str, pd.DataFrame],
    cfg: dict,
    metadata: dict[str, dict] | None = None,
) -> tuple[list[str], dict[str, list[str]]]:
    """对候选股票做准入过滤。

    Args:
        stocks: {code: 日线 DataFrame}，至少含 close/volume/amount；
                含 pre_close 时启用涨跌停过滤。
        cfg: 含 risk.min_avg_amount / min_list_days / min_market_cap。
        metadata: {code: {"market_cap", "is_st"}}，市值(元)/是否ST。
                  缺失的 code 视为通过市值/ST 过滤（mock 数据无该信息时）。

    Returns:
        (eligible, rejected)：通过的 code 列表，与
        {code: [拒绝原因, ...]} 映射。
    """
    risk = cfg["risk"]
    min_amount = risk.get("min_avg_amount", 0)
    min_days = risk.get("min_list_days", 0)
    min_cap = risk.get("min_market_cap", 0)
    metadata = metadata or {}

    eligible: list[str] = []
    rejected: dict[str, list[str]] = {}

    for code, df in stocks.items():
        reasons: list[str] = []

        if is_suspended(df):
            reasons.append("停牌")
        if is_limit_up(df, limit_pct=risk.get("limit_pct", 0.10)):
            reasons.append("涨停")
        if avg_amount(df) < min_amount:
            reasons.append(f"流动性不足(近20日均额 {avg_amount(df):,.0f} < {min_amount:,.0f})")
        if list_trading_days(df) < min_days:
            reasons.append(f"次新(上市{list_trading_days(df)}日 < {min_days}日)")

        meta = metadata.get(code, {})
        is_st = meta.get("is_st", False)
        if is_st:
            reasons.append("ST")
        cap = meta.get("market_cap")
        if cap is not None and cap < min_cap:
            reasons.append(f"市值不足({cap:,.0f} < {min_cap:,.0f})")

        if reasons:
            rejected[code] = reasons
        else:
            eligible.append(code)

    return eligible, rejected


def parse_rejected(rejected: dict[str, list[str]]) -> dict[str, list[str]]:
    """把拒绝映射序列化为易读的 {code: [原因]}（供看板/报告展示）。"""
    return {code: list(reasons) for code, reasons in rejected.items()}