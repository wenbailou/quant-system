import math

import pandas as pd

from src.tuning import grid_search, format_results_table


def _cfg():
    return {
        "data": {"source": "mock", "start_date": "2024-01-01",
                 "end_date": "2026-08-01"},
        "models": {"timing": {"predict_horizon_days": 5},
                   "selection": {"top_k": 4}},
        "risk": {"max_positions": 4, "single_stock_max": 0.25,
                 "total_position_max": 0.90, "stop_loss_pct": 0.08,
                 "trailing_stop_pct": 0.10, "take_profit_pct": 0.20},
        "position_levels": {"strong_bear": 0.0, "bear": 0.3,
                            "neutral": 0.6, "bull": 0.9},
    }


def test_grid_search_returns_sorted_results():
    param_grid = {"rebalance_freq": [10, 20], "min_train_days": [40, 60]}
    out = grid_search(_cfg(), param_grid=param_grid)
    results = out["results"]
    assert len(results) == 4
    # error 列始终存在；成功行为空字符串
    assert "error" in results.columns
    assert list(results.columns) == [
        "rebalance_freq", "min_train_days",
        "annualized_return", "max_drawdown", "sharpe_ratio", "score",
        "error",
    ]
    assert results["score"].is_monotonic_decreasing


def test_best_params_in_results():
    param_grid = {"rebalance_freq": [10, 20], "min_train_days": [40, 60]}
    out = grid_search(_cfg(), param_grid=param_grid)
    best = out["best_params"]
    assert best["rebalance_freq"] in [10, 20]
    assert best["min_train_days"] in [40, 60]
    assert out["best_score"] == out["results"].iloc[0]["score"]


def test_custom_score_fn():
    param_grid = {"rebalance_freq": [10], "min_train_days": [40]}
    out = grid_search(_cfg(), param_grid=param_grid,
                      score_fn=lambda m: m["annualized_return"])
    assert out["best_score"] == out["results"].iloc[0]["annualized_return"]


def test_config_not_mutated():
    cfg = _cfg()
    cfg_copy = {k: (v.copy() if isinstance(v, dict) else v) for k, v in cfg.items()}
    grid_search(cfg, param_grid={"rebalance_freq": [10], "min_train_days": [40]})
    # 基础配置不应被网格搜索修改
    assert cfg == cfg_copy


def test_all_failed_returns_empty_best():
    """全部参数组合失败时返回空 best_params 且不抛异常。"""
    bad_cfg = _cfg()
    bad_cfg["data"]["source"] = "nonexistent_source"
    out = grid_search(
        bad_cfg,
        param_grid={"rebalance_freq": [10], "min_train_days": [40]},
    )
    assert out["best_params"] == {}
    assert math.isnan(out["best_score"])
    # 错误信息应被捕获到 error 列
    assert out["results"]["error"].astype(str).str.len().all()


def test_score_fn_error_captured():
    """score_fn 抛异常时分数为 nan，错误信息进入 error 列。"""
    def bad_score(m):
        raise RuntimeError("boom")
    out = grid_search(
        _cfg(),
        param_grid={"rebalance_freq": [10], "min_train_days": [40]},
        score_fn=bad_score,
    )
    assert out["results"]["score"].isna().all()
    assert out["results"]["error"].astype(str).str.contains("score_fn error").all()


def test_format_results_table_markdown():
    results = pd.DataFrame([
        {"rebalance_freq": 10, "min_train_days": 40,
         "annualized_return": 0.05, "max_drawdown": 0.10,
         "sharpe_ratio": 0.5, "score": 0.5, "error": ""},
    ])
    md = format_results_table(results)
    assert "| rebalance_freq |" in md
    assert "| min_train_days |" in md
    assert "| score |" in md
    assert "0.5000" in md
    # 无错误时不显示 error 列
    assert "| error |" not in md


def test_format_results_table_with_error():
    results = pd.DataFrame([
        {"rebalance_freq": 10, "min_train_days": 40,
         "annualized_return": float("nan"), "max_drawdown": float("nan"),
         "sharpe_ratio": float("nan"), "score": float("nan"),
         "error": "loader failed"},
    ])
    md = format_results_table(results)
    assert "| error |" in md
    assert "loader failed" in md


def test_format_results_table_int_rendering():
    """参数整数列应原样渲染，不被转成浮点。"""
    results = pd.DataFrame([
        {"rebalance_freq": 10, "min_train_days": 40,
         "annualized_return": 0.05, "max_drawdown": 0.10,
         "sharpe_ratio": 0.5, "score": 0.5, "error": ""},
    ])
    md = format_results_table(results)
    # 整数 10 / 40 应直接出现，而非 10.0000
    assert "| 10 |" in md
    assert "| 40 |" in md
    assert "10.0000" not in md
