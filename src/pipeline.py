from src.data.factory import get_loader
from src.models.timing import TimingModel
from src.models.selection import SelectionModel
from src.strategy.portfolio import build_portfolio, apply_risk_pipeline
from src.backtest.engine import RiskBacktestEngine
from src.backtest.metrics import (
    annualized_return, max_drawdown, sharpe_ratio, win_rate, profit_factor,
)
from src.backtest.walkforward import (
    build_weight_schedule, walk_forward_nav, compute_benchmark,
)
from src.strategy.eligibility import screen_stocks, parse_rejected
from src.signals import build_daily_advice


def run_pipeline(
    cfg: dict,
    index_code: str = "000300.XSHG",
    stock_codes: list[str] | None = None,
    metadata: dict[str, dict] | None = None,
) -> dict:
    """端到端主流程：数据→特征→双模型→组合→风控→回测→指标→信号。

    返回 dict，含 position / picks / weights / nav / metrics / advice。

    注意：当前为简化的一次性直通回测——选股与择时使用全窗口数据，
    且引擎自首日起持有选定标的、无滚动调仓，存在前视偏差（look-ahead）。
    该结果仅用于演示流程，不应作为真实策略收益的估计。
    """
    loader = get_loader(cfg)

    index_df = loader.load_index(index_code)
    timing = TimingModel(cfg["models"]["timing"]["predict_horizon_days"])
    timing.fit(index_df)
    position = timing.predict_position(index_df, cfg["position_levels"])

    stock_codes = stock_codes or [f"60000{i}.XSHG" for i in range(1, 5)]
    stocks = {c: loader.load_stock(c) for c in stock_codes}
    eligible, rejected = screen_stocks(stocks, cfg, metadata=metadata)
    eligible_stocks = {c: stocks[c] for c in eligible}
    sel = SelectionModel(top_k=cfg["models"]["selection"]["top_k"])
    sel.fit(eligible_stocks)
    picks = sel.select(eligible_stocks)

    portfolio = build_portfolio(picks, position, cfg["risk"]["max_positions"])
    weights = apply_risk_pipeline(portfolio["weights"], cfg["risk"])

    engine = RiskBacktestEngine(
        initial_cash=1_000_000,
        stop_loss_pct=cfg["risk"]["stop_loss_pct"],
        trailing_stop_pct=cfg["risk"]["trailing_stop_pct"],
        take_profit_pct=cfg["risk"]["take_profit_pct"],
    )
    nav = engine.run(eligible_stocks, weights)

    advice = build_daily_advice(
        position=position,
        picks=picks,
        weights=weights,
        caution=f"建议仓位 {position * 100:.0f}%",
    )

    return {
        "position": position,
        "picks": picks,
        "weights": weights,
        "nav": nav,
        "rejected": parse_rejected(rejected),
        "metrics": {
            "annualized_return": annualized_return(nav),
            "max_drawdown": max_drawdown(nav),
            "sharpe_ratio": sharpe_ratio(nav),
        },
        "advice": advice,
    }


def run_walk_forward(
    cfg: dict,
    index_code: str = "000300.XSHG",
    stock_codes: list[str] | None = None,
    rebalance_freq: int = 20,
    min_train_days: int = 60,
    benchmark_codes: list[str] | None = None,
    metadata: dict[str, dict] | None = None,
) -> dict:
    """滚动调仓（walk-forward）回测：消除前视偏差。

    每个重平衡周期只用截至当天的历史数据生成信号，新权重自次日生效，
    定期调仓。返回净值曲线与绩效指标，可作为相对可信的策略收益估计。

    注意：walk-forward 为「权重 × 收益」逐日复利，未包含止损/止盈等
    盘中风控（与 run_pipeline 的 RiskBacktestEngine 口径不同），
    且采用"决策日收盘建仓、次日结算"的近似，结果用于相对比较而非绝对估计。
    回测已按 config 中 commission/stamp_duty/slippage 扣除交易成本。
    """
    loader = get_loader(cfg)
    index_df = loader.load_index(index_code)
    stock_codes = stock_codes or [f"60000{i}.XSHG" for i in range(1, 5)]
    stocks = {c: loader.load_stock(c) for c in stock_codes}

    schedule = build_weight_schedule(
        index_df, stocks, cfg,
        rebalance_freq=rebalance_freq, min_train_days=min_train_days,
        metadata=metadata,
    )
    cost_cfg = cfg["risk"]
    nav = walk_forward_nav(schedule, stocks, cost_cfg=cost_cfg)

    metrics = {
        "annualized_return": annualized_return(nav),
        "max_drawdown": max_drawdown(nav),
        "sharpe_ratio": sharpe_ratio(nav),
        "win_rate": win_rate(nav),
        "profit_factor": profit_factor(nav),
    }

    # 基准对比（沪深300 / 中证500），默认沪深300
    benchmark_codes = benchmark_codes or ["000300.XSHG"]
    benchmarks = {}
    for bcode in benchmark_codes:
        bdf = loader.load_index(bcode)
        bnav = (1 + bdf["close"].pct_change().fillna(0.0)).cumprod() * 1_000_000
        bnav.iloc[0] = 1_000_000
        benchmarks[bcode] = compute_benchmark(nav, bnav)

    return {
        "nav": nav,
        "weight_schedule": schedule,
        "metrics": metrics,
        "benchmarks": benchmarks,
    }