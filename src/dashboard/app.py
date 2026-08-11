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

tab1, tab2, tab3, tab4 = st.tabs(["大盘研判", "选股列表", "回测", "参数调优"])

with tab1:
    st.subheader("大盘择时信号")
    idx = loader.load_index("000300.XSHG")
    feats = build_features(idx)
    st.line_chart(feats["close"])
    model = TimingModel(cfg["models"]["timing"]["predict_horizon_days"])
    model.fit(idx)
    pos = model.predict_position(idx, cfg["position_levels"])
    st.metric("建议仓位", f"{pos * 100:.0f}%")

with tab2:
    st.subheader("候选股票")
    stocks = {f"60000{i}.XSHG": loader.load_stock(f"60000{i}.XSHG")
              for i in range(1, 5)}
    sel = SelectionModel(top_k=cfg["models"]["selection"]["top_k"])
    sel.fit(stocks)
    picks = sel.select(stocks)
    st.write(picks)

with tab3:
    st.subheader("滚动调仓回测（walk-forward，无前视偏差）")
    wf = run_walk_forward(loader_cfg)
    st.line_chart(wf["nav"])
    m = wf["metrics"]
    c1, c2, c3 = st.columns(3)
    c1.metric("年化收益", f"{m['annualized_return'] * 100:.2f}%")
    c2.metric("最大回撤", f"{m['max_drawdown'] * 100:.2f}%")
    c3.metric("夏普比率", f"{m['sharpe_ratio']:.2f}")
    st.caption("每 20 个交易日调仓，信号仅用截至当天的历史数据，次日生效。")

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