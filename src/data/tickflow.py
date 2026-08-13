"""TickFlow（tickflow.org）行情数据源。

TickFlow 提供 A 股/港股/美股统一 RESTful API + Python SDK（tickflow）。
SDK 的标的代码格式为 `600000.SH` / `000001.SZ`（带市场后缀），
与本系统使用的 `600000.XSHG` / `000001.XSHE` 不同，故在内部做映射。

API Key 通过环境变量 TICKFLOW_API_KEY 或构造参数 api_key 传入；
也可注入伪造 SDK 对象（tf 参数）用于测试，避免实际网络调用。

免费层限流 10 次/分钟：本模块使用进程级缓存（跨 loader 实例共享），
同一标的只请求一次；并在限流时自动等待重试。
"""
from __future__ import annotations

import os
import time

import pandas as pd

from src.data.base import MarketDataLoader

# 本系统代码后缀 → TickFlow 市场后缀
_SUFFIX_MAP = {
    "XSHG": "SH",
    "XSHE": "SZ",
    "XBEJ": "BJ",
}

# 进程级缓存：symbol → DataFrame（跨 loader 实例共享，避免重复请求）
_STOCK_CACHE: dict[str, pd.DataFrame] = {}
_META_CACHE: dict[str, dict] = {}

# 限流重试：最多重试次数与等待基础秒数
_MAX_RETRIES = 5
_RETRY_BASE_SECONDS = 30


def _is_rate_limit_error(exc: Exception) -> bool:
    """判断异常是否为限流错误。"""
    cls_name = type(exc).__name__.lower()
    return "ratelimit" in cls_name or "rate" in cls_name


def _to_tickflow_code(code: str) -> str:
    """把本系统代码（如 600000.XSHG）映射为 TickFlow 代码（600000.SH）。

    已是 TickFlow 格式（.SH/.SZ/.HK/.US）则原样返回。
    """
    if "." not in code:
        return code
    base, suffix = code.rsplit(".", 1)
    mapped = _SUFFIX_MAP.get(suffix.upper(), suffix)
    return f"{base}.{mapped}"


class TickFlowDataLoader(MarketDataLoader):
    """TickFlow 行情数据源。"""

    def __init__(
        self,
        start: str,
        end: str,
        api_key: str | None = None,
        tf=None,
    ):
        self.start = start
        self.end = end
        self._api_key = api_key or os.environ.get("TICKFLOW_API_KEY", "")
        self._tf = tf
        self._cached_tf = None

    def _get_tf(self):
        """返回 TickFlow 客户端：优先用注入对象，否则实例化真实 SDK。"""
        if self._cached_tf is not None:
            return self._cached_tf
        if self._tf is not None:
            self._cached_tf = self._tf
            return self._cached_tf
        try:
            from tickflow import TickFlow
        except ImportError as e:
            raise RuntimeError(
                "未安装 tickflow SDK，请先运行：pip install tickflow[all]"
            ) from e
        if not self._api_key:
            raise RuntimeError(
                "TickFlow 数据源未配置 API Key，请在环境变量 TICKFLOW_API_KEY "
                "中填写，或通过构造参数 api_key 传入。"
            )
        self._cached_tf = TickFlow(api_key=self._api_key)
        return self._cached_tf

    def _get_with_retry(self, fn, *args, **kwargs):
        """调用 tickflow 请求，遇限流自动等待重试。"""
        last_exc = None
        for attempt in range(_MAX_RETRIES):
            try:
                return fn(*args, **kwargs)
            except Exception as e:  # noqa: BLE001
                last_exc = e
                if not _is_rate_limit_error(e) or attempt == _MAX_RETRIES - 1:
                    raise
                # 限流：等待后重试（指数退避）
                wait = _RETRY_BASE_SECONDS * (attempt + 1)
                time.sleep(wait)
        raise last_exc

    def load_stock(self, code: str) -> pd.DataFrame:
        symbol = _to_tickflow_code(code)
        if symbol in _STOCK_CACHE:
            return _STOCK_CACHE[symbol].copy()
        # 单次最多 10000 根；用足够大的 count 覆盖自 start 起的全部日 K
        df = self._get_with_retry(
            self._get_tf().klines.get,
            symbol, period="1d", count=10000, as_dataframe=True,
        )
        if df is None or df.empty:
            return pd.DataFrame()
        out = df[["open", "high", "low", "close", "volume", "amount"]].copy()
        out.index = pd.to_datetime(df["trade_date"])
        # 按配置的时间范围过滤
        if self.start:
            out = out[out.index >= pd.Timestamp(self.start)]
        if self.end:
            out = out[out.index <= pd.Timestamp(self.end)]
        _STOCK_CACHE[symbol] = out
        return out.copy()

    def load_index(self, code: str) -> pd.DataFrame:
        return self.load_stock(code)

    def load_stock_metadata(self, code: str) -> dict:
        """返回准入过滤所需元数据（市值/上市日期/涨跌停价）。

        市值由 float_shares × 最新收盘价估算；ST 需结合名称判断
        （名称含 ST/*ST 视为 ST）。结果按 symbol 缓存。
        """
        symbol = _to_tickflow_code(code)
        if symbol in _META_CACHE:
            return dict(_META_CACHE[symbol])
        inst = self._get_with_retry(self._get_tf().instruments.get, symbol)
        if not inst:
            return {}
        ext = inst.get("ext", {}) or {}
        name = inst.get("name", "")
        # 最新收盘价用于市值估算（走缓存，不重复拉取）
        last_close = None
        try:
            df = self.load_stock(code)
            if len(df) > 0:
                last_close = float(df["close"].iloc[-1])
        except Exception:
            last_close = None
        float_shares = ext.get("float_shares")
        market_cap = float_shares * last_close if (
            float_shares and last_close
        ) else None
        meta = {
            "market_cap": market_cap,
            "list_date": ext.get("listing_date"),
            "is_st": "ST" in name.upper(),
            "limit_up": ext.get("limit_up"),
            "limit_down": ext.get("limit_down"),
        }
        _META_CACHE[symbol] = meta
        return dict(meta)