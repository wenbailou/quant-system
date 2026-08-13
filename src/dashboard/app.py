import sys
from pathlib import Path
from datetime import date
import streamlit as st

sys.path.append(str(Path(__file__).resolve().parents[2]))

from src.config import load_config
from src.models.timing import TimingModel
from src.models.selection import SelectionModel
from src.data.factory import get_loader
from src.features.pipeline import build_features
from src.pipeline import run_walk_forward
from src.tuning import grid_search, format_results_table

st.set_page_config(page_title="沪深量化系统", layout="wide")
cfg = load_config("config.yaml")

st.title("沪深量化交易分析系统")
st.caption("仅供研究参考，不构成投资建议")

with st.sidebar:
    start = st.date_input("起始日期", value=date(2020, 1, 1))
    end = st.date_input("结束日期", value=date.today())

loader_cfg = dict(cfg)
loader_cfg["data"] = dict(cfg["data"])
loader_cfg["data"]["start_date"] = str(start)
loader_cfg["data"]["end_date"] = str(end)
loader = get_loader(loader_cfg)

# 看板默认股票池：mock 用 600001-600004，真实数据用常见 A 股大票
DEFAULT_STOCKS = (
    ["600000.XSHG", "600519.XSHG", "600036.XSHG", "000001.XSHE",
     "600887.XSHG", "601899.XSHG"]
    if cfg["data"]["source"] != "mock"
    else [f"60000{i}.XSHG" for i in range(1, 5)]
)

tab1, tab2, tab3, tab4, tab5 = st.tabs(["大盘研判", "选股列表", "回测", "参数调优", "风控"])

with tab1:
    st.subheader("大盘择时信号")
    try:
        idx = loader.load_index("000300.XSHG")
        feats = build_features(idx)
        st.line_chart(feats["close"])
        model = TimingModel(cfg["models"]["timing"]["predict_horizon_days"])
        model.fit(idx)
        pos = model.predict_position(idx, cfg["position_levels"])
        st.metric("建议仓位", f"{pos * 100:.0f}%")
    except Exception as e:
        st.error(f"大盘数据加载失败：{e}")
        st.caption("请稍后刷新重试（TickFlow 免费层分钟级限流）")

with tab2:
    st.subheader("候选股票（经准入过滤）")
    from src.pipeline import run_pipeline
    try:
        res = run_pipeline(loader_cfg, stock_codes=DEFAULT_STOCKS)
        picks = res.get("picks", [])
        if picks:
            st.write(picks)
        else:
            st.info("当前无合格候选标的")
        rejected = res.get("rejected", {})
        if rejected:
            st.markdown("**被准入过滤剔除的标的**")
            st.table([{"代码": c, "剔除原因": "、".join(r)}
                      for c, r in rejected.items()])
    except Exception as e:
        st.error(f"选股列表加载失败：{e}")
        st.caption("请稍后刷新重试（TickFlow 免费层分钟级限流）")

with tab3:
    st.subheader("滚动调仓回测（walk-forward，扣交易成本，无前视偏差）")
    st.caption("该回测会加载全部候选股票并逐期训练模型，耗时较长且易触发数据源限流，请按需运行。")
    if st.button("运行回测", type="primary"):
        with st.spinner("正在运行回测，请稍候…"):
            try:
                wf = run_walk_forward(loader_cfg, stock_codes=DEFAULT_STOCKS)
            except Exception as e:
                st.error(f"回测运行失败：{e}")
                st.caption("可能是 TickFlow 免费层限流，请等待一分钟后重试。")
                st.stop()
        st.line_chart(wf["nav"])
        m = wf["metrics"]
        c1, c2, c3 = st.columns(3)
        c1.metric("年化收益", f"{m['annualized_return'] * 100:.2f}%")
        c2.metric("最大回撤", f"{m['max_drawdown'] * 100:.2f}%")
        c3.metric("夏普比率", f"{m['sharpe_ratio']:.2f}")
        if "win_rate" in m:
            c4, c5 = st.columns(2)
            c4.metric("胜率", f"{m['win_rate'] * 100:.1f}%")
            c5.metric("盈亏比", f"{m['profit_factor']:.2f}")
        # 基准对比
        benchmarks = wf.get("benchmarks", {})
        if benchmarks:
            st.markdown("**基准对比**")
            rows = []
            for bcode, bm in benchmarks.items():
                rows.append({
                    "基准": bcode,
                    "基准年化": f"{bm['bench_annualized_return'] * 100:.2f}%",
                    "基准回撤": f"{bm['bench_max_drawdown'] * 100:.2f}%",
                    "基准夏普": f"{bm['bench_sharpe_ratio']:.2f}",
                    "策略超额": f"{bm['excess_return'] * 100:.2f}%",
                })
            st.table(rows)
        st.caption("每 20 个交易日调仓，信号仅用截至当天的历史数据，次日生效；已扣佣金/印花税/滑点。")
    else:
        st.caption("点击上方「运行回测」按钮开始。")

with tab4:
    st.subheader("参数调优（walk-forward 网格搜索）")
    st.info("对重平衡频率与最小训练天数做网格搜索，按评分目标选出最优组合。")
    with st.form("tuning_form"):
        c1, c2, c3 = st.columns(3)
        rebalance_freqs = c1.multiselect(
            "rebalance_freq 候选（交易日）", [10, 20, 40, 60],
            default=[10, 20, 40])
        min_train_days = c2.multiselect(
            "min_train_days 候选", [40, 60, 120, 240],
            default=[40, 60, 120])
        score_target = c3.selectbox(
            "评分目标", ["sharpe", "return", "drawdown"])
        submitted = st.form_submit_button("运行网格搜索")

    if submitted:
        if not rebalance_freqs or not min_train_days:
            st.error("请至少选择一个 rebalance_freq 和一个 min_train_days 候选值。")
        else:
            score_map = {
                "sharpe": lambda m: m["sharpe_ratio"],
                "return": lambda m: m["annualized_return"],
                "drawdown": lambda m: -m["max_drawdown"],
            }
            with st.spinner("正在运行网格搜索，请稍候…"):
                out = grid_search(
                    loader_cfg,
                    index_code="000300.XSHG",
                    param_grid={
                        "rebalance_freq": rebalance_freqs,
                        "min_train_days": min_train_days,
                    },
                    score_fn=score_map[score_target],
                )
            if out["best_params"]:
                st.success(f"最优参数：{out['best_params']}"
                           f"　最优分数：{out['best_score']:.4f}")
                b1, b2, b3 = st.columns(3)
                b1.metric("年化收益",
                          f"{out['best_metrics']['annualized_return'] * 100:.2f}%")
                b2.metric("最大回撤",
                          f"{out['best_metrics']['max_drawdown'] * 100:.2f}%")
                b3.metric("夏普比率",
                          f"{out['best_metrics']['sharpe_ratio']:.2f}")
            else:
                st.error("所有参数组合均失败，请检查数据源或参数范围。")
            st.markdown(format_results_table(out["results"]))
    else:
        st.caption("配置上方参数后点击「运行网格搜索」，结果将在此展示。")

with tab5:
    st.subheader("组合级风控参数")
    risk = cfg["risk"]
    c1, c2, c3 = st.columns(3)
    c1.metric("单票仓位上限", f"{risk['single_stock_max'] * 100:.0f}%")
    c2.metric("行业集中度上限", f"{risk.get('industry_max', 0.30) * 100:.0f}%")
    c3.metric("现金比例下限", f"{risk.get('cash_min_ratio', 0.10) * 100:.0f}%")
    c4, c5, c6 = st.columns(3)
    c4.metric("持仓数量下限", f"{risk.get('min_positions', 5)} 只")
    c5.metric("持仓数量上限", f"{risk.get('max_positions', 15)} 只")
    c6.metric("最大回撤熔断", f"{risk.get('max_drawdown_circuit', 0.15) * 100:.0f}%")
    st.write("")
    st.markdown("**风控执行规则**")
    st.markdown(
        "- 单票止损：-{0:.0f}%，移动止损：自高点回撤 {1:.0f}%，止盈：+{2:.0f}%".format(
            risk['stop_loss_pct'] * 100, risk['trailing_stop_pct'] * 100,
            risk['take_profit_pct'] * 100))
    st.markdown(
        "- 组合风控流水线：单票上限 → 行业集中度 → 现金下限 → 持仓数下限"
        "（不足则空仓不建仓）")
    st.markdown(
        "- 最大回撤熔断：组合自高点回撤达 {0:.0f}% 时强制清仓至现金".format(
            risk.get('max_drawdown_circuit', 0.15) * 100))
    st.caption("组合级风控在回测引擎中实时执行，与选股准入过滤共同构成完整风控体系。")