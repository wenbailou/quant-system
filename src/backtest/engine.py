import pandas as pd


class BacktestEngine:
    """简化事件驱动回测：按每日涨跌幅更新组合净值。"""

    def __init__(self, initial_cash: float = 1_000_000):
        self.initial_cash = initial_cash

    def run(self, price_df: pd.DataFrame, weights: dict) -> pd.Series:
        rets = price_df["close"].pct_change().fillna(0.0)
        portfolio_ret = sum(
            w * rets for w in weights.values()
        ) if weights else pd.Series(0.0, index=price_df.index)
        nav = (1 + portfolio_ret).cumprod() * self.initial_cash
        nav.iloc[0] = self.initial_cash
        return nav