# 沪深量化交易系统

半自动量化分析系统：每日大盘研判、仓位建议、候选股票推荐与历史回测。

## 快速开始

```bash
pip install -r requirements.txt
python -m pytest -v
python -m streamlit run src/dashboard/app.py
```

## 数据源

当前使用模拟数据源（`MockMarketDataLoader`），接入聚宽/优矿/通联时替换
`src/data/loader.py` 中的实现即可，接口保持不变。

## 免责声明

本系统仅供研究参考，不构成投资建议，无法保证盈利。