import pandas as pd
from src.data.base import MarketDataLoader


class JoinQuantDataLoader(MarketDataLoader):
    """聚宽（jqdatasdk）行情数据源。

    需在 config.yaml 的 data.joinquant 中配置账号密码。未配置凭证时
    load_stock/load_index 会抛出 RuntimeError，提示用户填写凭证。
    也可通过参数 `jq` 注入一个伪造的 SDK 对象（用于测试），
    避免在无凭证环境下实际调用聚宽接口。
    """

    def __init__(
        self,
        start: str,
        end: str,
        account: str,
        password: str,
        jq=None,
    ):
        self.start = start
        self.end = end
        self.account = account
        self.password = password
        self._jq = jq

    def _get_jq(self):
        if self._jq is None:
            try:
                import jqdatasdk as jq
            except ImportError as e:
                raise RuntimeError(
                    "未安装 jqdatasdk，请先运行：pip install jqdatasdk"
                ) from e
            self._jq = jq
        return self._jq

    def _auth(self):
        if not self.account or not self.password:
            raise RuntimeError(
                "聚宽数据源未配置账号密码，请在 config.yaml 的 "
                "data.joinquant 中填写 account / password。"
            )
        self._get_jq().auth(self.account, self.password)

    def load_stock(self, code: str) -> pd.DataFrame:
        jq = self._get_jq()
        self._auth()
        raw = jq.get_price(
            code,
            start_date=self.start,
            end_date=self.end,
            frequency="daily",
            fields=["open", "close", "high", "low", "volume", "money"],
            fq="pre",
        )
        if raw is None or raw.empty:
            return pd.DataFrame()
        df = raw.rename(columns={"money": "amount"})
        cols = ["open", "high", "low", "close", "volume", "amount"]
        return df[cols]

    def load_index(self, code: str) -> pd.DataFrame:
        return self.load_stock(code)

    def load_stock_metadata(self, code: str) -> dict:
        """聚宽元数据（市值/上市日期/ST）接入的占位实现。

        当前返回空 dict，表示不启用市值/次新/ST 过滤（口径与 mock 一致
        时，仅流动性/停牌/涨跌停过滤生效）。后续可通过聚宽
        get_fundamentals / get_stock_info 等接口补齐真实字段。
        """
        return {}