import math

import pytest

from src.strategy.risk import (
    enforce_single_stock_limit,
    apply_stop_loss,
    enforce_industry_concentration,
    enforce_cash_min_ratio,
    enforce_min_positions,
    evaluate_circuit_breaker,
)


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


def test_industry_concentration_caps_overweight_industry():
    weights = {"A": 0.20, "B": 0.20, "C": 0.20}  # 总仓位 0.6
    industry_map = {"A": "银行", "B": "医药", "C": "银行"}
    out = enforce_industry_concentration(weights, industry_map, industry_max=0.30)
    # 银行行业总权重 0.40 > 0.30，应缩至 0.30
    bank = sum(w for c, w in out.items() if industry_map[c] == "银行")
    assert bank <= 0.30 + 1e-9
    # 超额部分转为现金，总仓位下降
    assert abs(sum(out.values()) - 0.5) < 1e-6  # 0.2(医药) + 0.3(银行压缩后)


def test_industry_concentration_keeps_under_limit():
    weights = {"A": 0.1, "B": 0.1, "C": 0.1}
    industry_map = {"A": "银行", "B": "医药", "C": "银行"}
    out = enforce_industry_concentration(weights, industry_map, industry_max=0.30)
    bank = sum(w for c, w in out.items() if industry_map[c] == "银行")
    assert bank <= 0.30 + 1e-9
    assert abs(sum(out.values()) - 0.3) < 1e-6


def test_cash_min_ratio_reduces_position():
    weights = {"A": 0.9, "B": 0.1}  # 总仓位 1.0，现金 0
    out = enforce_cash_min_ratio(weights, cash_min_ratio=0.10)
    # 现金应 ≥ 0.1，即总仓位 ≤ 0.9
    assert abs(sum(out.values()) - 0.9) < 1e-6


def test_cash_min_ratio_no_change_when_enough_cash():
    weights = {"A": 0.5, "B": 0.3}  # 现金 0.2 ≥ 0.1
    out = enforce_cash_min_ratio(weights, cash_min_ratio=0.10)
    assert abs(sum(out.values()) - 0.8) < 1e-6


def test_min_positions_blocks_when_too_few():
    weights = {"A": 0.6, "B": 0.3}  # 2 只 < 3
    out = enforce_min_positions(weights, min_positions=3)
    assert out == {}  # 风控优先，不建仓


def test_min_positions_keeps_when_enough():
    weights = {"A": 0.3, "B": 0.3, "C": 0.3}
    out = enforce_min_positions(weights, min_positions=3)
    assert len(out) == 3
    assert abs(sum(out.values()) - 0.9) < 1e-6


def test_circuit_breaker_not_triggered():
    peak = 1_000_000
    current = 900_000  # 回撤 10% < 15%
    assert evaluate_circuit_breaker(peak, current, threshold=0.15) is False


def test_circuit_breaker_triggered():
    peak = 1_000_000
    current = 800_000  # 回撤 20% ≥ 15%
    assert evaluate_circuit_breaker(peak, current, threshold=0.15) is True