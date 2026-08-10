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
from src.pipeline import run_pipeline

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

tab1, tab2, tab3 = st.tabs(["大盘研判", "选股列表", "回测"])

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
    st.subheader("回测结果")
    result = run_pipeline(loader_cfg)
    st.line_chart(result["nav"])
    m = result["metrics"]
    c1, c2, c3 = st.columns(3)
    c1.metric("年化收益", f"{m['annualized_return'] * 100:.2f}%")
    c2.metric("最大回撤", f"{m['max_drawdown'] * 100:.2f}%")
    c3.metric("夏普比率", f"{m['sharpe_ratio']:.2f}")
    st.write("候选标的", result["picks"])
    st.caption(result["advice"]["caution"])