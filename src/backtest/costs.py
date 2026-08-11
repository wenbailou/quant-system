"""交易成本与基准对比。

在 walk-forward 回测中，权重表逐日变化即代表调仓。成交成本按
换手仓位收取：单边换手 turnover = Σ|w_t − w_{t-1}|，近似买入量 =
卖出量 = turnover / 2。据此计算佣金（双边）、印花税（仅卖出）、
滑点（双边）。此外提供与基准（沪深300 / 中证500）的超额收益对比。
"""
from __future__ import annotations

import numpy as np
import pandas as pd


def turnover(weight_schedule: pd.DataFrame) -> pd.Series:
    """计算逐日单边换手率：当日目标权重相对前一日的变动之和。

    首日返回 0（视为建仓基准，不重复计费）。换手率同时覆盖买入与卖出，
    故称"单边换手"（买卖合计幅度）。
    """
    diff = weight_schedule.diff().fillna(0.0)
    tv = diff.abs().sum(axis=1)
    tv.iloc[0] = 0.0
    return tv


def cost_rate(single_sided_turnover: float, cfg: dict) -> float:
    """给定单边换手率，计算当日成交成本占组合净值的比例。

    设买入量 = 卖出量 = single_sided_turnover / 2：
      - 佣金（双边）：买卖均收取 → cost *= commission
      - 印花税（仅卖出）：卖出部分 * stamp_duty
      - 滑点（双边）：买卖均收取 → cost *= slippage
    """
    if single_sided_turnover <= 0:
        return 0.0
    buy_amt = sell_amt = single_sided_turnover / 2
    commission = cfg.get("commission", 0.0)
    stamp_duty = cfg.get("stamp_duty", 0.0)
    slippage = cfg.get("slippage", 0.0)
    return (buy_amt * 2 * commission
            + sell_amt * stamp_duty
            + (buy_amt + sell_amt) * slippage)


def apply_costs(
    nav: pd.Series,
    weight_schedule: pd.DataFrame,
    cfg: dict,
) -> pd.Series:
    """按换手率扣除交易成本，返回扣成本后的净值序列。

    采用"逐日收益 × (1 - 成本率)"的方式在净值上扣费，避免对首日
    重复计费（首日 turnover 为 0，成本为 0）。
    """
    tv = turnover(weight_schedule)
    rate = tv.apply(lambda v: cost_rate(v, cfg))
    rets = nav.pct_change().fillna(0.0)
    net_rets = rets * (1 - rate)
    start = nav.iloc[0]
    net_nav = (1 + net_rets).cumprod() * start
    net_nav.iloc[0] = start
    return net_nav


def compute_benchmark_excess(
    strat_nav: pd.Series,
    bench_nav: pd.Series,
) -> float:
    """计算策略相对基准的累计超额收益（几何差）。

    超额收益 = (1 + 策略累计收益) / (1 + 基准累计收益) - 1。
    """
    strat_ret = strat_nav.iloc[-1] / strat_nav.iloc[0] - 1
    bench_ret = bench_nav.iloc[-1] / bench_nav.iloc[0] - 1
    return float((1 + strat_ret) / (1 + bench_ret) - 1)


def benchmark_returns(
    bench_nav: pd.Series,
    strat_nav: pd.Series,
) -> dict:
    """计算基准的绩效指标，用于报告对比。"""
    from src.backtest.metrics import annualized_return, max_drawdown, sharpe_ratio
    return {
        "annualized_return": annualized_return(bench_nav),
        "max_drawdown": max_drawdown(bench_nav),
        "sharpe_ratio": sharpe_ratio(bench_nav),
        "excess_return": compute_benchmark_excess(strat_nav, bench_nav),
    }