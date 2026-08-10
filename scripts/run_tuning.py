import argparse
import sys
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parents[1]))

from src.config import load_config
from src.tuning import grid_search, format_results_table


def main():
    parser = argparse.ArgumentParser(description="参数调优：walk-forward 网格搜索")
    parser.add_argument("--config", default="config.yaml", help="配置文件路径")
    parser.add_argument("--index", default="000300.XSHG", help="指数代码")
    parser.add_argument("--stocks", nargs="*", default=None, help="候选股票代码列表")
    parser.add_argument("--rebalance-freqs", nargs="*", type=int,
                        default=[10, 20, 40], help="重平衡频率候选值")
    parser.add_argument("--min-train-days", nargs="*", type=int,
                        default=[40, 60, 120], help="最小训练天数候选值")
    parser.add_argument("--score", default="sharpe",
                        choices=["sharpe", "return", "drawdown"],
                        help="评分目标（越大越好；drawdown 取负值）")
    parser.add_argument("--output", default=None, help="输出 Markdown 路径")
    args = parser.parse_args()

    cfg = load_config(args.config)
    stocks = args.stocks or ["600000.XSHG", "600519.XSHG",
                             "600036.XSHG", "000001.XSHE"]

    score_map = {
        "sharpe": lambda m: m["sharpe_ratio"],
        "return": lambda m: m["annualized_return"],
        "drawdown": lambda m: -m["max_drawdown"],
    }

    param_grid = {
        "rebalance_freq": args.rebalance_freqs,
        "min_train_days": args.min_train_days,
    }
    out = grid_search(cfg, index_code=args.index, stock_codes=stocks,
                      param_grid=param_grid, score_fn=score_map[args.score])

    print("=== 网格搜索结果 ===")
    print(format_results_table(out["results"]))
    print()
    print(f"最优参数: {out['best_params']}")
    print(f"最优分数: {out['best_score']:.4f}")
    print(f"最优指标: {out['best_metrics']}")

    if args.output:
        Path(args.output).parent.mkdir(parents=True, exist_ok=True)
        Path(args.output).write_text(
            format_results_table(out["results"]), encoding="utf-8")
        print(f"对比表已导出：{args.output}")


if __name__ == "__main__":
    main()
