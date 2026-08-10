from src.data.factory import get_loader
from src.models.timing import TimingModel
from src.models.selection import SelectionModel
from src.strategy.portfolio import build_portfolio, apply_risk_pipeline
from src.backtest.engine import RiskBacktestEngine
from src.backtest.metrics import annualized_return, max_drawdown, sharpe_ratio
from src.signals import build_daily_advice


def run_pipeline(
    cfg: dict,
    index_code: str = "000300.XSHG",
    stock_codes: list[str] | None = None,
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
    sel = SelectionModel(top_k=cfg["models"]["selection"]["top_k"])
    sel.fit(stocks)
    picks = sel.select(stocks)

    portfolio = build_portfolio(picks, position, cfg["risk"]["max_positions"])
    weights = apply_risk_pipeline(portfolio["weights"], cfg["risk"])

    engine = RiskBacktestEngine(
        initial_cash=1_000_000,
        stop_loss_pct=cfg["risk"]["stop_loss_pct"],
        trailing_stop_pct=cfg["risk"]["trailing_stop_pct"],
        take_profit_pct=cfg["risk"]["take_profit_pct"],
    )
    nav = engine.run(stocks, weights)

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
        "metrics": {
            "annualized_return": annualized_return(nav),
            "max_drawdown": max_drawdown(nav),
            "sharpe_ratio": sharpe_ratio(nav),
        },
        "advice": advice,
    }