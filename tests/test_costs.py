import pandas as pd

from src.backtest.costs import (
    turnover,
    cost_rate,
    apply_costs,
    compute_benchmark_excess,
)


def test_turnover_computes_weighted_change():
    w = pd.DataFrame({
        "600001": [0.0, 0.3, 0.3, 0.0],
        "600002": [0.0, 0.3, 0.3, 0.0],
    })
    tv = turnover(w)
    # 首次建仓：0.3+0.3=0.6；保持：0；清仓：0.6
    assert tv.iloc[0] == 0.0   # 首日无调仓（沿用前一日）
    assert abs(tv.iloc[1] - 0.6) < 1e-9
    assert abs(tv.iloc[2]) < 1e-9
    assert abs(tv.iloc[3] - 0.6) < 1e-9


def test_cost_rate_uses_config():
    cfg = {"commission": 0.00025, "stamp_duty": 0.0005, "slippage": 0.001}
    # 单边换手 1.0（买 0.5 + 卖 0.5）
    rate = cost_rate(1.0, cfg)
    expected = 1.0 * 0.00025 + 0.5 * 0.0005 + 1.0 * 0.001
    assert abs(rate - expected) < 1e-12


def test_apply_costs_reduces_nav():
    # 有收益的净值：第二日 +10%，若有 0.6 换手，扣费后应低于无成本 +10% 净值
    nav = pd.Series([1_000_000, 1_100_000, 1_100_000])
    w = pd.DataFrame({
        "600001": [0.0, 0.3, 0.3],
        "600002": [0.0, 0.3, 0.3],
    })
    cfg = {"commission": 0.00025, "stamp_duty": 0.0005, "slippage": 0.001}
    nav_after = apply_costs(nav, w, cfg)
    # 第二日有 0.6 换手，扣费后应低于无成本净值
    assert nav_after.iloc[1] < nav.iloc[1]
    # 首日无换手，成本为 0，不受影响
    assert nav_after.iloc[0] == nav.iloc[0]


def test_compute_benchmark_excess():
    strat = pd.Series([1_000_000, 1_100_000, 1_210_000])
    bench = pd.Series([1_000_000, 1_050_000, 1_100_000])
    # 策略累计收益高于基准，超额应 > 0
    excess = compute_benchmark_excess(strat, bench)
    assert excess > 0