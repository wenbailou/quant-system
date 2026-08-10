import argparse
import sys
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parents[1]))

from src.config import load_config
from src.reporting import export_daily_report


def main():
    parser = argparse.ArgumentParser(description="导出每日下单信号 Markdown 报告")
    parser.add_argument("--config", default="config.yaml", help="配置文件路径")
    parser.add_argument("--output", default=None, help="输出 Markdown 路径（默认 reports/daily_日期.md）")
    parser.add_argument("--date", default=None, help="报告日期（默认今天）")
    parser.add_argument("--index", default="000300.XSHG", help="指数代码")
    parser.add_argument("--stocks", nargs="*", default=None,
                        help="候选股票代码列表（默认 600000/600519/600036/000001 等）")
    args = parser.parse_args()

    cfg = load_config(args.config)
    stocks = args.stocks or ["600000.XSHG", "600519.XSHG",
                             "600036.XSHG", "000001.XSHE"]
    path = export_daily_report(
        cfg, output_path=args.output, report_date=args.date,
        index_code=args.index, stock_codes=stocks,
    )
    print(f"报告已导出：{path}")


if __name__ == "__main__":
    main()