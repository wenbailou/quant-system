from src.data.base import MarketDataLoader
from src.data.loader import MockMarketDataLoader
from src.data.joinquant import JoinQuantDataLoader


def get_loader(cfg: dict) -> MarketDataLoader:
    """根据配置返回对应的行情数据源。

    通过 config.yaml 的 `data.source` 切换数据源：mock | joinquant。
    未指定时默认使用 mock。
    """
    data_cfg = cfg["data"]
    source = data_cfg.get("source", "mock")
    start = data_cfg.get("start_date", "2016-01-01")
    end = data_cfg.get("end_date", "2026-08-01")

    if source == "mock":
        return MockMarketDataLoader(start=start, end=end)

    if source == "joinquant":
        jq_cfg = data_cfg.get("joinquant", {})
        return JoinQuantDataLoader(
            start=start,
            end=end,
            account=jq_cfg.get("account", ""),
            password=jq_cfg.get("password", ""),
        )

    raise ValueError(f"未知数据源: {source}（可选 mock / joinquant）")