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


class RiskBacktestEngine:
    """多资产事件驱动回测：逐日对每个持仓应用风控。

    每个持仓按目标权重在首日买入，逐日检查：
    - 固定止损：相对建仓价回撤超过 stop_loss_pct 则卖出
    - 移动止损：自入场后最高点回撤超过 trailing_stop_pct 则卖出
    - 止盈：相对建仓价涨幅超过 take_profit_pct 则卖出
    卖出回笼资金计入现金，未持仓部分为现金。
    """

    def __init__(
        self,
        initial_cash: float = 1_000_000,
        stop_loss_pct: float = 0.08,
        trailing_stop_pct: float = 0.10,
        take_profit_pct: float = 0.20,
    ):
        self.initial_cash = initial_cash
        self.stop_loss_pct = stop_loss_pct
        self.trailing_stop_pct = trailing_stop_pct
        self.take_profit_pct = take_profit_pct

    def run(self, prices: dict[str, pd.DataFrame],
            weights: dict[str, float]) -> pd.Series:
        closes = {code: df["close"] for code, df in prices.items()}
        close_df = pd.concat(closes, axis=1).sort_index()
        dates = close_df.index

        cash = self.initial_cash
        positions = {}
        for code, w in weights.items():
            if w <= 0 or code not in close_df.columns:
                continue
            entry = float(close_df[code].iloc[0])
            if entry <= 0:
                continue
            target_value = w * self.initial_cash
            cash -= target_value
            shares = target_value / entry
            positions[code] = {"shares": shares, "entry": entry, "high": entry}

        nav = []
        for dt in dates:
            for code, pos in list(positions.items()):
                price = float(close_df.at[dt, code])
                if price != price:  # NaN（停牌）当日跳过风控
                    continue
                pos["high"] = max(pos["high"], price)
                if self._should_sell(pos, price):
                    cash += pos["shares"] * price
                    del positions[code]

            held_value = 0.0
            for code, pos in positions.items():
                price = float(close_df.at[dt, code])
                if price == price:
                    held_value += pos["shares"] * price
            nav.append(cash + held_value)

        return pd.Series(nav, index=dates)

    def _should_sell(self, pos: dict, price: float) -> bool:
        entry = pos["entry"]
        if (entry - price) / entry >= self.stop_loss_pct:
            return True
        high = pos["high"]
        if high > 0 and (high - price) / high >= self.trailing_stop_pct:
            return True
        if (price - entry) / entry >= self.take_profit_pct:
            return True
        return False