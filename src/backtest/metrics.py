import numpy as np
import pandas as pd


def annualized_return(nav: pd.Series, periods_per_year: int = 252) -> float:
    n = len(nav)
    if n < 2:
        return 0.0
    total = nav.iloc[-1] / nav.iloc[0]
    return float(total ** (periods_per_year / (n - 1)) - 1)


def max_drawdown(nav: pd.Series) -> float:
    running_max = nav.cummax()
    drawdown = (nav - running_max) / running_max
    return float(-drawdown.min())


def sharpe_ratio(nav: pd.Series, rf: float = 0.0, periods_per_year: int = 252) -> float:
    rets = nav.pct_change().dropna()
    if len(rets) < 2 or rets.std() == 0:
        return 0.0
    return float((rets.mean() - rf / periods_per_year) / rets.std()
                 * (periods_per_year ** 0.5))


def win_rate(nav: pd.Series) -> float:
    """胜率：日收益为正的交易日占比（不含零收益）。"""
    rets = nav.pct_change().dropna()
    gains = rets[rets > 0]
    non_zero = rets[rets != 0]
    if len(non_zero) == 0:
        return 0.0
    return float(len(gains) / len(non_zero))


def profit_factor(nav: pd.Series) -> float:
    """盈亏比：盈利日收益之和 / 亏损日收益绝对值之和。"""
    rets = nav.pct_change().dropna()
    gross_profit = float(rets[rets > 0].sum())
    gross_loss = float(-rets[rets < 0].sum())
    if gross_loss == 0:
        return float("inf") if gross_profit > 0 else 0.0
    return gross_profit / gross_loss


def turnover_rate(prev_weights, next_weights) -> float:
    """单期换手率：两期权重向量差的绝对值之和。"""
    return float(np.abs(np.asarray(next_weights) - np.asarray(prev_weights)).sum())


def excess_return(strat_nav: pd.Series, bench_nav: pd.Series) -> float:
    """策略相对基准的累计超额收益（几何差）。"""
    strat_ret = strat_nav.iloc[-1] / strat_nav.iloc[0] - 1
    bench_ret = bench_nav.iloc[-1] / bench_nav.iloc[0] - 1
    return float((1 + strat_ret) / (1 + bench_ret) - 1)