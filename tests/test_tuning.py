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
    assert list(results.columns) == [
        "rebalance_freq", "min_train_days",
        "annualized_return", "max_drawdown", "sharpe_ratio", "score",
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


def test_format_results_table_markdown():
    results = pd.DataFrame([
        {"rebalance_freq": 10, "min_train_days": 40,
         "annualized_return": 0.05, "max_drawdown": 0.10,
         "sharpe_ratio": 0.5, "score": 0.5},
    ])
    md = format_results_table(results)
    assert "| rebalance_freq |" in md
    assert "| min_train_days |" in md
    assert "| score |" in md
    assert "0.5000" in md
