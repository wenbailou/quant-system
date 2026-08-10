import pandas as pd
from src.models.timing import TimingModel
from src.models.selection import SelectionModel
from src.strategy.portfolio import build_portfolio, apply_risk_pipeline


def _signal(index_trail: pd.DataFrame, stock_trail: dict[str, pd.DataFrame],
            cfg: dict) -> dict[str, float]:
    """在重平衡日基于截至当天的历史数据生成目标权重。"""
    position = (
        TimingModel(cfg["models"]["timing"]["predict_horizon_days"])
        .fit(index_trail)
        .predict_position(index_trail, cfg["position_levels"])
    )
    sel = SelectionModel(top_k=cfg["models"]["selection"]["top_k"])
    sel.fit(stock_trail)
    picks = sel.select(stock_trail)
    portfolio = build_portfolio(picks, position, cfg["risk"]["max_positions"])
    return apply_risk_pipeline(portfolio["weights"], cfg["risk"])


def build_weight_schedule(
    index_df: pd.DataFrame,
    stocks: dict[str, pd.DataFrame],
    cfg: dict,
    rebalance_freq: int = 20,
    min_train_days: int = 60,
) -> pd.DataFrame:
    """生成每日目标权重表（消除前视偏差）。

    每 rebalance_freq 个交易日为一个重平衡周期：在重平衡日收盘后，
    仅用截至当天的数据（index_trail / stock_trail）重新生成信号与权重。
    新权重自**下一个交易日**起生效，避免"当天决策 + 当天成交"的同日泄漏。

    返回 DataFrame，行=日期，列=股票代码，值为该日持仓权重（0 表示现金）。
    """
    dates = list(index_df.index)
    decisions: dict[pd.Timestamp, dict[str, float]] = {}
    for i, d in enumerate(dates):
        if i < min_train_days:
            continue
        if (i - min_train_days) % rebalance_freq == 0:
            idx_trail = index_df.loc[:d]
            stock_trail = {c: df.loc[:d] for c, df in stocks.items()}
            decisions[d] = _signal(idx_trail, stock_trail, cfg)

    schedule: dict[pd.Timestamp, dict[str, float]] = {}
    active: dict[str, float] = {}
    rebalance_list = sorted(decisions)
    di = 0
    for d in dates:
        while di < len(rebalance_list) and rebalance_list[di] < d:
            active = decisions[rebalance_list[di]]
            di += 1
        schedule[d] = dict(active)
    return pd.DataFrame(schedule).T


def walk_forward_nav(
    weight_schedule: pd.DataFrame,
    stocks: dict[str, pd.DataFrame],
    initial_cash: float = 1_000_000,
) -> pd.Series:
    """按权重表计算组合净值序列。权重表与个股 close 需按日期对齐。"""
    close_df = pd.DataFrame(
        {c: df["close"] for c, df in stocks.items()}
    ).sort_index()
    rets = close_df.pct_change().fillna(0.0)
    w = weight_schedule.reindex(rets.index).fillna(0.0)
    portfolio_ret = (w * rets).sum(axis=1)
    nav = (1 + portfolio_ret).cumprod() * initial_cash
    nav.iloc[0] = initial_cash
    return nav