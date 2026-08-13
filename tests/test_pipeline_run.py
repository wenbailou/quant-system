import pandas as pd
from src.pipeline import run_pipeline


def _cfg():
    return {
        "data": {"source": "mock", "start_date": "2020-01-01",
                 "end_date": "2020-06-01"},
        "models": {"timing": {"predict_horizon_days": 5},
                   "selection": {"top_k": 3}},
        "risk": {"max_positions": 3, "single_stock_max": 0.15,
                 "total_position_max": 0.90, "stop_loss_pct": 0.08,
                 "trailing_stop_pct": 0.10, "take_profit_pct": 0.20,
                 "min_avg_amount": 0, "min_list_days": 0,
                 "min_market_cap": 3_000_000_000},
        "position_levels": {"strong_bear": 0.0, "bear": 0.3,
                            "neutral": 0.6, "bull": 0.9},
    }


def test_run_pipeline_returns_structure():
    result = run_pipeline(_cfg())
    assert "position" in result
    assert 0.0 <= result["position"] <= 0.9
    assert set(result["metrics"]) == {
        "annualized_return", "max_drawdown", "sharpe_ratio"}
    assert isinstance(result["nav"], pd.Series)
    assert len(result["nav"]) > 0
    assert isinstance(result["picks"], list)
    assert isinstance(result["weights"], dict)
    assert "advice" in result


def test_run_pipeline_applies_metadata_eligibility():
    """显式传入 metadata 时，市值/ST 过滤应在选股前生效。"""
    cfg = _cfg()
    codes = ["600000.XSHG", "600001.XSHG"]
    meta = {
        "600000.XSHG": {"market_cap": 1e9, "is_st": False},   # 市值不足
        "600001.XSHG": {"market_cap": 1e12, "is_st": True},   # ST
    }
    result = run_pipeline(cfg, stock_codes=codes, metadata=meta)
    # 两只均被剔除 → 无候选
    assert result["picks"] == []
    assert "600000.XSHG" in result["rejected"]
    assert "600001.XSHG" in result["rejected"]
    # 空候选时净值仍为正常长度（不崩溃）
    assert len(result["nav"]) > 0