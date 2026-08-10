import os
import sys
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parents[1]))

from src.config import load_config
from src.data.factory import get_loader
from src.pipeline import run_walk_forward


def main():
    assert os.environ.get("JQ_ACCOUNT") and os.environ.get("JQ_PASSWORD"), \
        "缺少环境变量 JQ_ACCOUNT / JQ_PASSWORD"

    cfg = load_config("config.yaml")
    cfg["data"]["source"] = "joinquant"
    # 账号权限窗口：2025-05-02 ~ 2026-05-09
    cfg["data"]["start_date"] = "2025-06-01"
    cfg["data"]["end_date"] = "2026-05-01"

    loader = get_loader(cfg)
    print("=== 指数 000300.XSHG ===")
    idx = loader.load_index("000300.XSHG")
    print("shape:", idx.shape)
    print(idx.head(2))
    print(idx.tail(2))

    codes = ["600000.XSHG", "600519.XSHG", "600036.XSHG", "000001.XSHE"]
    print("=== 个股 ===")
    for c in codes:
        df = loader.load_stock(c)
        print(c, "shape:", df.shape, "cols:", list(df.columns),
              "last_close:", round(float(df["close"].iloc[-1]), 2))

    print("=== run_walk_forward ===")
    res = run_walk_forward(cfg, index_code="000300.XSHG", stock_codes=codes,
                           rebalance_freq=20, min_train_days=60)
    print("nav len:", len(res["nav"]))
    print("nav head:", [round(v, 2) for v in res["nav"].head(3).tolist()])
    print("nav tail:", [round(v, 2) for v in res["nav"].tail(3).tolist()])
    print("metrics:", {k: round(v, 4) for k, v in res["metrics"].items()})
    print("LIVE INTEGRATION OK")


if __name__ == "__main__":
    main()