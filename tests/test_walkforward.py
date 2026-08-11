import pandas as pd
import pytest
from src.backtest.walkforward import build_weight_schedule, walk_forward_nav


def _cfg():
    return {
        "data": {"source": "mock", "start_date": "2020-01-01",
                 "end_date": "2020-06-01"},
        "models": {"timing": {"predict_horizon_days": 5},
                   "selection": {"top_k": 3}},
        "risk": {"max_positions": 3, "single_stock_max": 0.15,
                 "total_position_max": 0.90},
        "position_levels": {"strong_bear": 0.0, "bear": 0.3,
                            "neutral": 0.6, "bull": 0.9},
    }


def _data():
    from src.data.loader import MockMarketDataLoader
    loader = MockMarketDataLoader("2020-01-01", "2020-06-01")
    index_df = loader.load_index("000300.XSHG")
    stocks = {f"60000{i}.XSHG": loader.load_stock(f"60000{i}.XSHG")
              for i in range(1, 5)}
    return index_df, stocks


def test_no_signal_before_first_rebalance():
    index_df, stocks = _data()
    min_train = 40
    schedule = build_weight_schedule(
        index_df, stocks, _cfg(), rebalance_freq=10, min_train_days=min_train)
    # 首个重平衡决策前，权重应全为 0（全现金，无前视）
    early = schedule.iloc[:min_train]
    assert (early.abs().sum(axis=1) == 0).all()


def test_walk_forward_nav_shape():
    index_df, stocks = _data()
    schedule = build_weight_schedule(
        index_df, stocks, _cfg(), rebalance_freq=10, min_train_days=40)
    nav = walk_forward_nav(schedule, stocks)
    assert isinstance(nav, pd.Series)
    assert len(nav) == len(index_df)
    assert nav.iloc[0] == pytest.approx(1_000_000)


def test_weights_apply_from_day_after_decision(monkeypatch):
    index_df, stocks = _data()
    min_train = 40

    def fake_signal(idx_trail, stock_trail, cfg):
        return {"600000.XSHG": 0.5}

    monkeypatch.setattr("src.backtest.walkforward._signal", fake_signal)
    schedule = build_weight_schedule(
        index_df, stocks, _cfg(), rebalance_freq=10, min_train_days=min_train)
    # 决策日（索引 min_train 那天）当天仍为现金，次日才生效 → 无同日泄漏
    assert schedule.iloc[min_train].abs().sum() == 0
    assert schedule.iloc[min_train + 1]["600000.XSHG"] == 0.5


def test_signal_only_sees_data_up_to_decision_day(monkeypatch):
    index_df, stocks = _data()
    min_train = 40
    captured = {}

    def spy_signal(idx_trail, stock_trail, cfg):
        if "idx_last" not in captured:
            captured["idx_last"] = idx_trail.index[-1]
            captured["stock_last"] = {
                c: df.index[-1] for c, df in stock_trail.items()}
        return {"600000.XSHG": 0.5}

    monkeypatch.setattr("src.backtest.walkforward._signal", spy_signal)
    build_weight_schedule(index_df, stocks, _cfg(),
                          rebalance_freq=10, min_train_days=min_train)
    first_decision_date = index_df.index[min_train]
    # 首次决策生成的信号，其训练数据必须截止于决策日当天 → 无前视
    assert captured["idx_last"] == first_decision_date
    assert all(v == first_decision_date for v in captured["stock_last"].values())


def test_min_train_exceeding_data_raises():
    """min_train_days 超过数据长度时应抛出明确错误（而非返回平坦净值 0 分）。

    该场景无法生成任何重平衡决策，若静默返回 0 分会在网格搜索中被误判
    为有效最优参数，故必须显式报错。
    """
    index_df, stocks = _data()
    with pytest.raises(ValueError, match="min_train_days"):
        build_weight_schedule(
            index_df, stocks, _cfg(),
            rebalance_freq=10, min_train_days=10_000)