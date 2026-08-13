import argparse
import sys
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parents[1]))

from src.config import load_config
from src.data.factory import get_loader
from src.models.selection import SelectionModel, MIN_TRAIN_SAMPLES


def main():
    parser = argparse.ArgumentParser(description="选股模型训练")
    parser.add_argument("--config", default="config.yaml", help="配置文件路径")
    parser.add_argument("--index", default="000300.XSHG", help="指数代码")
    parser.add_argument("--stocks", nargs="*", default=None,
                        help="候选股票代码列表（默认浦发/茅台/招行/平安）")
    parser.add_argument("--label-horizon", type=int, default=5,
                        help="未来收益预测标签周期（交易日）")
    parser.add_argument("--top-k", type=int, default=10, help="选股数量")
    parser.add_argument("--train-start", default=None, help="训练期起始日期（覆盖 config）")
    parser.add_argument("--output", default="models/selection.joblib",
                        help="模型输出路径")
    args = parser.parse_args()

    cfg = load_config(args.config)
    if args.train_start:
        cfg["data"]["start_date"] = args.train_start
    stocks_codes = args.stocks or ["600000.XSHG", "600519.XSHG",
                                   "600036.XSHG", "000001.XSHE"]

    loader = get_loader(cfg)
    stocks = {c: loader.load_stock(c) for c in stocks_codes}
    # 剔除空数据
    stocks = {c: df for c, df in stocks.items() if not df.empty}
    if not stocks:
        print("错误：所有股票数据为空，请检查数据源与股票代码。")
        sys.exit(1)

    model = SelectionModel(top_k=args.top_k, label_horizon=args.label_horizon)
    model.fit(stocks)

    if model._trained:
        # 训练样本量
        X, y = model._build_training_data(stocks, args.label_horizon)
        print(f"=== 选股模型训练完成 ===")
        print(f"训练样本数: {len(X)}")
        print(f"特征维度: {list(X.columns)}")
        print(f"标签周期: {args.label_horizon} 交易日（未来收益）")
        print(f"Top-K: {args.top_k}")
        Path(args.output).parent.mkdir(parents=True, exist_ok=True)
        model.save(args.output)
        print(f"模型已保存: {args.output}")
    else:
        print(f"警告：训练样本不足 {MIN_TRAIN_SAMPLES}，模型未训练，"
              f"将退化为动量排序。")
        print("提示：请扩大训练期或增加候选股票数量。")
        sys.exit(2)


if __name__ == "__main__":
    main()