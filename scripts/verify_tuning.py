"""参数调优深入验证脚本。

覆盖：
1. 确定性/可复现性：同一输入多次运行结果一致
2. 前视偏差：决策日权重次日生效（真实信号，非 monkeypatch）
3. 评分函数一致性：best_score 应等于该评分目标下的全网格最值
4. 边界场景：空网格、单值、重复值、min_train_days 过大
5. NaN 指标时的排序与 best 选择
"""
import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.append(str(Path(__file__).resolve().parents[1]))

from src.config import load_config
from src.tuning import grid_search
from src.backtest.walkforward import build_weight_schedule
from src.data.loader import MockMarketDataLoader


def make_cfg() -> dict:
    cfg = load_config("config.yaml")
    cfg["data"]["source"] = "mock"
    cfg["data"]["start_date"] = "2020-01-01"
    cfg["data"]["end_date"] = "2021-01-01"
    return cfg


def load_data(cfg):
    loader = MockMarketDataLoader(cfg["data"]["start_date"], cfg["data"]["end_date"])
    index_df = loader.load_index("000300.XSHG")
    stocks = {f"60000{i}.XSHG": loader.load_stock(f"60000{i}.XSHG")
              for i in range(1, 5)}
    return index_df, stocks


def check_determinism(cfg):
    pg = {"rebalance_freq": [10, 20], "min_train_days": [40, 60]}
    r1 = grid_search(cfg, param_grid=pg)["results"]
    r2 = grid_search(cfg, param_grid=pg)["results"]
    assert r1.equals(r2), "确定性失败：两次运行结果不一致"
    print("[OK] 确定性：同一输入两次运行结果完全一致")


def check_lookahead(cfg):
    """用真实信号验证"决策日当天不提前生效"（无同日泄漏）。

    前视偏差的本质：决策日基于当日收盘数据生成的信号，不得在决策日
    当天成交（否则等于用收盘数据提前交易）。因此决策日当天的权重必须
    与决策前一日完全一致，新权重只能从决策日之后才可能生效。
    注：信号本身可能预测空仓（0 权重），故不要求次日必有持仓。
    """
    index_df, stocks = load_data(cfg)
    min_train = 40
    schedule = build_weight_schedule(
        index_df, stocks, cfg, rebalance_freq=10, min_train_days=min_train)
    dates = list(index_df.index)
    # 对所有决策日：当天权重 == 前一日权重（不得在决策日提前调仓）
    decision_idx = [i for i in range(min_train, len(dates))
                    if (i - min_train) % 10 == 0]
    for i in decision_idx:
        d = dates[i]
        prev = dates[i - 1]
        cur = schedule.loc[d]
        before = schedule.loc[prev]
        assert cur.equals(before), \
            f"决策日 {d.date()} 权重与前一交易日不一致，存在同日泄漏"
    # 决策日之后应存在某日权重与决策日不同（证明决策确实生效）
    changed = (schedule.diff().abs().sum(axis=1) > 0).any()
    assert changed, "整个调度表无任何调仓，可能未正确生效"
    print(f"[OK] 前视偏差：{len(decision_idx)} 个决策日均未在决策日提前调仓")


def check_score_consistency(cfg):
    """best_score 应等于该评分目标下全网格的最值。"""
    pg = {"rebalance_freq": [10, 20], "min_train_days": [40]}
    out = grid_search(cfg, param_grid=pg, score_fn=lambda m: m["sharpe_ratio"])
    max_score = out["results"]["score"].max()
    assert abs(out["best_score"] - max_score) < 1e-9, \
        "best_score 与全网格最大分数不一致"
    # best_params 应匹配分数最高行
    best_row = out["results"].iloc[0]
    assert out["best_params"]["rebalance_freq"] == best_row["rebalance_freq"]
    assert out["best_params"]["min_train_days"] == best_row["min_train_days"]
    print("[OK] 评分一致性：best_score=全网格最值，best_params 与最高分行一致")


def check_empty_grid(cfg):
    """空网格应返回 1 行（空组合），不崩溃。"""
    out = grid_search(cfg, param_grid={})
    assert len(out["results"]) == 1, "空网格应恰好 1 行"
    assert out["best_params"] == {}, "空网格 best_params 应为空"
    print("[OK] 空网格：返回 1 行，best_params 为空")


def check_single_value(cfg):
    """单值网格应正常返回。"""
    out = grid_search(cfg, param_grid={"rebalance_freq": [10],
                                        "min_train_days": [40]})
    assert len(out["results"]) == 1
    assert out["best_params"] == {"rebalance_freq": 10, "min_train_days": 40}
    print("[OK] 单值网格：返回 1 行，best_params 正确")  


def check_duplicate_values(cfg):
    """重复候选值应产生重复行但不崩溃。"""
    out = grid_search(cfg, param_grid={"rebalance_freq": [10, 10],
                                        "min_train_days": [40]})
    assert len(out["results"]) == 2, "重复值应产生 2 行"
    print("[OK] 重复值：产生 2 行，不崩溃")


def check_large_min_train(cfg):
    """min_train_days 大于数据长度：应被识别为无效参数而非返回 0 分。

    该场景下无法生成任何重平衡决策，walk-forward 应抛错并让网格搜索
    将该组合标记为失败（score=NaN、error 有内容），而不是以 0 分混入
    有效候选并被误选为最优。
    """
    out = grid_search(cfg, param_grid={"rebalance_freq": [10],
                                        "min_train_days": [5000]})
    assert len(out["results"]) == 1
    row = out["results"].iloc[0]
    # 应被标记为无效：score 为 NaN，error 有内容，best_params 为空
    assert np.isnan(row["score"]), "超大 min_train_days 不应返回 0 分"
    assert row["error"], "超大 min_train_days 应被标记 error"
    assert out["best_params"] == {}, "超大 min_train_days 不应被选为最优"
    print("[OK] 超大 min_train_days：被标记为无效，不参与最优选择")


def check_all_nan_metrics(cfg, monkeypatch_free=True):
    """构造全 NaN 指标（模拟全部失败），验证排序与空 best。"""
    # 用非法数据源触发全部失败
    bad = dict(cfg)
    bad["data"] = dict(cfg["data"])
    bad["data"]["source"] = "_nonexistent_"
    out = grid_search(bad, param_grid={"rebalance_freq": [10, 20],
                                        "min_train_days": [40]})
    assert out["best_params"] == {}, "全失败应返回空 best_params"
    assert np.isnan(out["best_score"]), "全失败 best_score 应为 NaN"
    # 失败行应沉底（排在最后）
    assert out["results"]["score"].isna().all()
    # error 列应有内容
    assert out["results"]["error"].astype(str).str.len().all()
    print("[OK] 全 NaN：排序正确、best 为空、error 已捕获")


def main():
    cfg = make_cfg()
    checks = [
        ("确定性", check_determinism),
        ("前视偏差", check_lookahead),
        ("评分一致性", check_score_consistency),
        ("空网格", check_empty_grid),
        ("单值", check_single_value),
        ("重复值", check_duplicate_values),
        ("超大min_train", check_large_min_train),
        ("全NaN指标", check_all_nan_metrics),
    ]
    for name, fn in checks:
        fn(cfg)
    print(f"\n全部 {len(checks)} 项调优验证通过 ✅")


if __name__ == "__main__":
    main()