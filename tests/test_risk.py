from src.strategy.risk import enforce_single_stock_limit, apply_stop_loss


def test_enforce_single_stock_limit():
    position = 0.20
    limit = 0.15
    assert enforce_single_stock_limit(position, limit) == 0.15


def test_apply_stop_loss_triggered():
    entry = 10.0
    current = 9.0
    stop_loss_pct = 0.08
    assert apply_stop_loss(entry, current, stop_loss_pct) is True


def test_apply_stop_loss_not_triggered():
    entry = 10.0
    current = 9.5
    stop_loss_pct = 0.08
    assert apply_stop_loss(entry, current, stop_loss_pct) is False