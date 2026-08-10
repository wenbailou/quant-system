from src.strategy.risk import enforce_single_stock_limit


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


def apply_risk_pipeline(weights: dict[str, float], cfg: dict) -> dict[str, float]:
    limit = cfg["single_stock_max"]
    capped = {c: enforce_single_stock_limit(w, limit) for c, w in weights.items()}
    total = sum(capped.values())
    if total > cfg["total_position_max"]:
        scale = cfg["total_position_max"] / total
        capped = {c: w * scale for c, w in capped.items()}
    return capped