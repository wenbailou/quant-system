# 沪深量化交易系统

半自动量化分析系统：每日大盘择时、仓位建议、候选股票推荐、组合级风控与历史回测。
支持模拟数据与真实 A 股行情（TickFlow / 聚宽），提供可视化看板与每日报告。

> 仅供研究参考，不构成投资建议，无法保证盈利。

## 功能概览

- **大盘择时**：基于沪深 300 技术指标，输出强空/空/震荡/多/强多五档仓位建议
- **标的准入过滤**：剔除流动性不足、微盘股、ST、次新股、停牌、涨跌停标的
- **选股模型**：随机森林回归学习「特征 → 未来收益」，预测预期收益并取 Top-K
- **组合级风控**：单票上限、行业集中度、现金下限、持仓数下限、最大回撤熔断
- **回测引擎**：单票止损/移动止损/止盈 + 组合熔断，行为 walk-forward（扣交易成本、无前视偏差）
- **参数调优**：walk-forward 网格搜索，按夏普/收益/回撤自动选优
- **可视化看板**：大盘 / 选股 / 回测 / 调优 / 风控 五个标签页
- **每日报告**：导出 Markdown 信号报告（仓位、候选、被过滤标的、风控纪律、绩效）

## 快速开始

```bash
pip install -r requirements.txt
python -m pytest -v
python -m streamlit run src/dashboard/app.py
```

## 数据源

系统通过 `config.yaml` 的 `data.source` 切换数据源（`mock` | `tickflow` | `joinquant`），
未指定时默认使用模拟数据源（`MockMarketDataLoader`，便于无凭证开发）。

### 使用 TickFlow 真实 A 股数据（推荐）

1. 安装 SDK：`pip install "tickflow[all]"`
2. 在 [tickflow.org](https://tickflow.org/) 注册并获取 API Key
3. 用环境变量传入（避免凭证入库）：

```powershell
$env:TICKFLOW_API_KEY = "你的 API Key"
```

4. 切换数据源并启动看板：

```bash
# config.yaml 中设置 data.source: "tickflow"
python -m streamlit run src/dashboard/app.py
```

> TickFlow 提供 A 股/港股/美股实时行情与日 K 全量历史，免费层即可用于日级别回测。
> 代码格式：个股 `600000.SH`、`000001.SZ`、指数 `000300.SH`（系统内部自动映射代码后缀）。

### 使用聚宽（JoinQuant）真实数据

1. 安装聚宽 SDK：`pip install jqdatasdk`
2. 配置凭证并切换数据源（二选一）：
   - 推荐用环境变量：`JQ_ACCOUNT` / `JQ_PASSWORD`
   - 或在 `config.yaml` 中填写 `data.joinquant.account` / `password`
3. 启动看板后，行情将从前复权日线真实拉取。

> 聚宽代码需带交易所后缀，如个股 `600000.XSHG`、指数 `000300.XSHG`。
> 未填写凭证时，`JoinQuantDataLoader` 会抛出明确的 RuntimeError 提示，不会静默失败。

### 自定义数据源

新增数据源只需实现 `src/data/base.py` 的 `MarketDataLoader` 接口
（`load_stock` / `load_index` / `load_stock_metadata`），并在
`src/data/factory.py` 的 `get_loader` 中注册即可，上层代码无需改动。

## 选股模型训练

模型默认在回测/pipeline 运行时基于历史数据自动训练（适用 walk-forward 的无前视要求）。
也可通过脚本一次性训练并持久化到磁盘：

```bash
python scripts/train_selection.py \
  --stocks 600000.XSHG 600519.XSHG 600036.XSHG 000001.XSHE \
  --train-start 2018-01-01 \
  --output models/selection.joblib
```

加载已训练模型：

```python
from src.models.selection import SelectionModel
model = SelectionModel.load("models/selection.joblib")
picks = model.select(stocks)
```

## 风控体系

| 层级 | 规则 | 配置项 |
|---|---|---|
| 标的准入 | 流动性≥5000万、非微盘、非ST、非次新、非停牌、非涨跌停 | `risk.min_avg_amount` 等 |
| 单票级 | 固定止损 / 移动止损 / 止盈 | `risk.stop_loss_pct` 等 |
| 组合级 | 单票上限 / 行业集中度 / 现金下限 / 持仓数下限 | `risk.single_stock_max` 等 |
| 组合级 | 最大回撤熔断：自高点回撤达阈值强制清仓 | `risk.max_drawdown_circuit` |

## 目录结构

```
quant-system/
├── config.yaml            # 全局配置（数据源、模型、风控参数）
├── src/
│   ├── data/              # 数据源：base/loader(mock)/tickflow/joinquant/factory
│   ├── features/          # 特征工程：SMA/收益率/RSI
│   ├── models/            # 择时(TimingModel) 与 选股(SelectionModel)
│   ├── strategy/          # 准入过滤、组合构建、风控
│   ├── backtest/          # 回测引擎、绩效指标、walk-forward
│   ├── dashboard/         # Streamlit 看板
│   ├── reporting.py       # Markdown 报告生成
│   └── pipeline.py        # 端到端主流程
├── scripts/               # 训练/调优/报告导出脚本
└── tests/                 # pytest 测试套件
```

## 免责声明

本系统仅供研究参考，不构成投资建议，无法保证盈利。历史回测不代表未来表现。