def enforce_single_stock_limit(position_size: float, limit: float) -> float:
    """单票仓位上限约束。"""
    return min(position_size, limit)


def apply_stop_loss(entry_price: float, current_price: float, stop_loss_pct: float) -> bool:
    """判断是否触发固定止损。"""
    drawdown = (entry_price - current_price) / entry_price
    return drawdown >= stop_loss_pct


def apply_trailing_stop(high_since_entry: float, current_price: float, trailing_pct: float) -> bool:
    """判断是否触发移动止损。"""
    drawdown_from_high = (high_since_entry - current_price) / high_since_entry
    return drawdown_from_high >= trailing_pct


def apply_take_profit(entry_price: float, current_price: float, take_profit_pct: float) -> bool:
    return (current_price - entry_price) / entry_price >= take_profit_pct


def enforce_industry_concentration(
    weights: dict[str, float],
    industry_map: dict[str, str],
    industry_max: float,
) -> dict[str, float]:
    """行业集中度约束：单一行业累计权重不超过 industry_max。

    若某行业超限，按比例压缩该行业内所有标的权重，使行业权重回到上限；
    被压缩的部分转为现金（不放大其他行业，保持相对比例）。
    """
    if not weights:
        return {}
    # 统计各行业当前权重
    industry_weight: dict[str, float] = {}
    for code, w in weights.items():
        ind = industry_map.get(code, "其他")
        industry_weight[ind] = industry_weight.get(ind, 0.0) + w
    # 计算各行业缩放系数
    scale = {
        ind: min(1.0, industry_max / w) if w > 0 else 1.0
        for ind, w in industry_weight.items()
    }
    out = {}
    for code, w in weights.items():
        ind = industry_map.get(code, "其他")
        out[code] = w * scale.get(ind, 1.0)
    return out


def enforce_cash_min_ratio(
    weights: dict[str, float],
    cash_min_ratio: float,
) -> dict[str, float]:
    """现金比例下限：总仓位不超过 1 - cash_min_ratio。

    若当前总仓位过高（现金不足），按比例整体缩减各标的权重。
    """
    if not weights:
        return {}
    total = sum(weights.values())
    max_position = 1 - cash_min_ratio
    if total <= max_position:
        return dict(weights)
    scale = max_position / total
    return {c: w * scale for c, w in weights.items()}


def enforce_min_positions(
    weights: dict[str, float],
    min_positions: int,
) -> dict[str, float]:
    """持仓数量下限：至少 min_positions 只才允许建仓。

    若标的数不足 min_positions，返回空权重（风控优先，不建仓），
    避免少数标的过于集中。
    """
    if not weights:
        return {}
    if len(weights) < min_positions:
        return {}
    return dict(weights)


def evaluate_circuit_breaker(
    peak_nav: float,
    current_nav: float,
    threshold: float,
) -> bool:
    """最大回撤熔断：组合自高点回撤超过 threshold 则触发。"""
    if peak_nav <= 0:
        return False
    drawdown = (peak_nav - current_nav) / peak_nav
    return drawdown >= threshold