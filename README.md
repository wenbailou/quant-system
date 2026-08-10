# 沪深量化交易系统

半自动量化分析系统：每日大盘研判、仓位建议、候选股票推荐与历史回测。

## 快速开始

```bash
pip install -r requirements.txt
python -m pytest -v
python -m streamlit run src/dashboard/app.py
```

## 数据源

系统通过 `config.yaml` 的 `data.source` 切换数据源（`mock` | `joinquant`），
未指定时默认使用模拟数据源（`MockMarketDataLoader`，便于无凭证开发）。

### 使用聚宽（JoinQuant）真实数据

1. 安装聚宽 SDK：`pip install jqdatasdk`
2. 在 `config.yaml` 中填写账号密码并切换数据源：

```yaml
data:
  source: "joinquant"
  joinquant:
    account: "你的聚宽账号"
    password: "你的密码"
```

3. 启动看板后，行情将从前复权日线真实拉取：
   `python -m streamlit run src/dashboard/app.py`

> 提示：聚宽代码需带交易所后缀，如个股 `600000.XSHG`、指数 `000300.XSHG`。
> 未填写凭证时，`JoinQuantDataLoader` 会抛出明确的 RuntimeError 提示，不会静默失败。

### 自定义数据源

新增数据源只需实现 `src/data/base.py` 的 `MarketDataLoader` 接口
（`load_stock` / `load_index`），并在 `src/data/factory.py` 的 `get_loader`
中注册即可，上层代码无需改动。

## 免责声明

本系统仅供研究参考，不构成投资建议，无法保证盈利。