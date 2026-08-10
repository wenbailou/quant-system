from src.strategy.portfolio import build_portfolio, apply_risk_pipeline


def test_build_portfolio_respects_top_k():
    picks = ["600001", "600002", "600003", "600004"]
    position = 0.9
    portfolio = build_portfolio(picks, position, max_positions=3)
    assert len(portfolio["weights"]) == 3
    assert abs(sum(portfolio["weights"].values()) - position) < 1e-6


def test_apply_risk_pipeline_caps_single():
    cfg = {"single_stock_max": 0.15, "total_position_max": 0.90}
    weights = {"600001": 0.5, "600002": 0.5}
    out = apply_risk_pipeline(weights, cfg)
    assert max(out.values()) <= 0.15