import os
from src.data.base import MarketDataLoader
from src.data.loader import MockMarketDataLoader
from src.data.joinquant import JoinQuantDataLoader
from src.data.tickflow import TickFlowDataLoader


def _from_env_or_config(jq_cfg: dict, key: str, env_name: str) -> str:
    """优先取环境变量，其次取 config，避免把真实凭证写入配置文件。"""
    return os.environ.get(env_name) or jq_cfg.get(key, "")


def get_loader(cfg: dict) -> MarketDataLoader:
    """根据配置返回对应的行情数据源。

    通过 config.yaml 的 `data.source` 切换数据源：mock | joinquant。
    未指定时默认使用 mock。聚宽凭证优先从环境变量读取，
    其次从 config.yaml 的 data.joinquant 读取。
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
            account=_from_env_or_config(jq_cfg, "account", "JQ_ACCOUNT"),
            password=_from_env_or_config(jq_cfg, "password", "JQ_PASSWORD"),
        )

    if source == "tickflow":
        tf_cfg = data_cfg.get("tickflow", {})
        return TickFlowDataLoader(
            start=start,
            end=end,
            api_key=_from_env_or_config(tf_cfg, "api_key", "TICKFLOW_API_KEY"),
        )

    raise ValueError(f"未知数据源: {source}（可选 mock / joinquant / tickflow）")