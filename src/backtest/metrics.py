import numpy as np
import pandas as pd


def annualized_return(nav: pd.Series, periods_per_year: int = 252) -> float:
    n = len(nav)
    if n < 2:
        return 0.0
    total = nav.iloc[-1] / nav.iloc[0]
    return float(total ** (periods_per_year / (n - 1)) - 1)


def max_drawdown(nav: pd.Series) -> float:
    running_max = nav.cummax()
    drawdown = (nav - running_max) / running_max
    return float(-drawdown.min())


def sharpe_ratio(nav: pd.Series, rf: float = 0.0, periods_per_year: int = 252) -> float:
    rets = nav.pct_change().dropna()
    if len(rets) < 2 or rets.std() == 0:
        return 0.0
    return float((rets.mean() - rf / periods_per_year) / rets.std()
                 * (periods_per_year ** 0.5))