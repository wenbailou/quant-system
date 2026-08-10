"""参数调优：对 walk-forward 回测做网格搜索，输出对比表并选出最优组合。

优化目标默认为夏普比率（风险调整后收益），可在调用时切换为
年化收益或最大回撤。仅搜索 walk-forward 参数（rebalance_freq /
min_train_days），风控参数因 RiskBacktestEngine 口径不同暂不纳入。
"""
from __future__ import annotations

import copy
import itertools
from typing import Callable

import pandas as pd

from src.pipeline import run_walk_forward


def grid_search(
    base_cfg: dict,
    index_code: str = "000300.XSHG",
    stock_codes: list[str] | None = None,
    param_grid: dict | None = None,
    score_fn: Callable[[dict[str, float]], float] | None = None,
) -> dict:
    """对 walk-forward 参数做网格搜索。

    Args:
        base_cfg: 基础配置（会被深拷贝，不修改原对象）。
        param_grid: 参数网格，键为参数名（rebalance_freq / min_train_days），
                    值为候选列表。默认搜索常见范围。
        score_fn: 评分函数，输入 metrics dict，返回标量分数，越大越好。
                  默认取 sharpe_ratio。

    Returns:
        dict: {
            "results": DataFrame（每行一组参数 + 指标 + 分数），
            "best_params": 最优参数 dict,
            "best_score": 最优分数,
            "best_metrics": 最优组合的指标 dict,
        }
    """
    if param_grid is None:
        param_grid = {
            "rebalance_freq": [10, 20, 40],
            "min_train_days": [40, 60, 120],
        }

    if score_fn is None:
        score_fn = lambda m: m["sharpe_ratio"]

    keys = list(param_grid.keys())
    combos = list(itertools.product(*[param_grid[k] for k in keys]))

    records: list[dict] = []
    for combo in combos:
        params = dict(zip(keys, combo))
        cfg = copy.deepcopy(base_cfg)
        try:
            res = run_walk_forward(
                cfg,
                index_code=index_code,
                stock_codes=stock_codes,
                rebalance_freq=params.get("rebalance_freq", 20),
                min_train_days=params.get("min_train_days", 60),
            )
            metrics = res["metrics"]
        except Exception as exc:
            metrics = {
                "annualized_return": float("nan"),
                "max_drawdown": float("nan"),
                "sharpe_ratio": float("nan"),
                "error": str(exc),
            }
        score = score_fn(metrics)
        row = {
            **params,
            "annualized_return": metrics.get("annualized_return", float("nan")),
            "max_drawdown": metrics.get("max_drawdown", float("nan")),
            "sharpe_ratio": metrics.get("sharpe_ratio", float("nan")),
            "score": score,
        }
        records.append(row)

    results = pd.DataFrame(records)
    results = results.sort_values("score", ascending=False).reset_index(drop=True)

    best = results.iloc[0]
    best_params = {k: int(best[k]) for k in keys}
    return {
        "results": results,
        "best_params": best_params,
        "best_score": float(best["score"]),
        "best_metrics": {
            "annualized_return": float(best["annualized_return"]),
            "max_drawdown": float(best["max_drawdown"]),
            "sharpe_ratio": float(best["sharpe_ratio"]),
        },
    }


def format_results_table(results: pd.DataFrame) -> str:
    """把网格搜索结果格式化为 Markdown 对比表。"""
    cols = [c for c in results.columns if c != "error"]
    header = "| " + " | ".join(cols) + " |"
    sep = "| " + " | ".join(["---"] * len(cols)) + " |"
    lines = [header, sep]
    for _, row in results.iterrows():
        cells = []
        for c in cols:
            v = row[c]
            if isinstance(v, float):
                cells.append(f"{v:.4f}")
            else:
                cells.append(str(v))
        lines.append("| " + " | ".join(cells) + " |")
    return "\n".join(lines)
