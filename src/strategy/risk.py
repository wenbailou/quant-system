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