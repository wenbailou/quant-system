from src.strategy.risk import (
    enforce_single_stock_limit,
    enforce_industry_concentration,
    enforce_cash_min_ratio,
    enforce_min_positions,
)


def build_portfolio(picks: list[str], total_position: float,
                    max_positions: int) -> dict:
    n = min(len(picks), max_positions)
    if n == 0:
        return {"stocks": [], "weights": {}}
    weight_each = total_position / n
    return {
        "stocks": picks[:n],
        "weights": {c: weight_each for c in picks[:n]},
    }


def apply_risk_pipeline(
    weights: dict[str, float],
    cfg: dict,
    industry_map: dict[str, str] | None = None,
) -> dict[str, float]:
    """组合级风控流水线：单票上限→行业集中度→现金下限→持仓数下限。"""
    limit = cfg.get("single_stock_max", 1.0)
    capped = {c: enforce_single_stock_limit(w, limit) for c, w in weights.items()}

    # 行业集中度
    if industry_map:
        capped = enforce_industry_concentration(
            capped, industry_map, cfg.get("industry_max", 1.0)
        )

    # 现金比例下限
    capped = enforce_cash_min_ratio(capped, cfg.get("cash_min_ratio", 0.0))

    # 持仓数量下限（不足则空仓）
    capped = enforce_min_positions(capped, cfg.get("min_positions", 1))

    return capped