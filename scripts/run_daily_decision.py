import argparse
import sys
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parents[1]))

from src.config import load_config
from src.dashboard.decision import build_full_report
from src.dashboard.notify import push_all
from src.pipeline import run_pipeline, run_walk_forward


def main():
    parser = argparse.ArgumentParser(description="生成并推送每日决策仪表盘")
    parser.add_argument("--config", default="config.yaml", help="配置文件路径")
    parser.add_argument("--index", default="000300.XSHG", help="指数代码")
    parser.add_argument("--stocks", nargs="*", default=None,
                        help="候选股票代码列表（默认 6 只真实大票）")
    parser.add_argument("--date", default=None, help="报告日期（默认今天）")
    parser.add_argument("--output", default=None, help="输出 Markdown 路径")
    parser.add_argument("--no-push", action="store_true", help="不推送，仅生成报告")
    parser.add_argument("--html", default=None,
                        help="同时生成静态网页并输出到该路径（默认 reports/dashboard_日期.html）")
    parser.add_argument("--skip-walkforward", action="store_true",
                        help="跳过耗时的 walk-forward 回测（减少限流）")
    parser.add_argument("--wecom", default=None, help="企业微信 webhook")
    parser.add_argument("--feishu", default=None, help="飞书 webhook")
    args = parser.parse_args()

    cfg = load_config(args.config)
    stocks = args.stocks or ["600000.XSHG", "600519.XSHG", "600036.XSHG",
                             "000001.XSHE", "600887.XSHG", "601899.XSHG"]
    report_date = args.date or __import__("datetime").date.today().isoformat()

    print("→ 运行端到端流水线（真实数据）...")
    result = run_pipeline(cfg, index_code=args.index, stock_codes=stocks)
    if not args.skip_walkforward:
        print("→ 运行 walk-forward 回测（可能较慢）...")
        wf = run_walk_forward(cfg, index_code=args.index, stock_codes=stocks)
        result["metrics"] = wf["metrics"]
        result["benchmarks"] = wf.get("benchmarks", {})
        result["advice"]["caution"] = (
            f"建议仓位 {result.get('position', 0) * 100:.0f}%"
        )

    md = build_full_report(result, cfg, report_date=report_date)
    output = args.output or f"reports/decision_{report_date}.md"
    Path(output).parent.mkdir(parents=True, exist_ok=True)
    Path(output).write_text(md, encoding="utf-8")
    print(f"✓ 报告已生成：{output}")

    if args.html is not False:
        from src.dashboard.web import render_dashboard_html
        html_path = args.html or f"reports/dashboard_{report_date}.html"
        html = render_dashboard_html(result, cfg, report_date=report_date)
        Path(html_path).parent.mkdir(parents=True, exist_ok=True)
        Path(html_path).write_text(html, encoding="utf-8")
        print(f"✓ 网页已生成：{html_path}")

    if not args.no_push:
        print("→ 推送决策仪表盘...")
        from src.dashboard.decision import build_decision_dashboard
        dashboard = build_decision_dashboard(result, cfg, report_date=report_date)
        results = push_all(dashboard, wecom_webhook=args.wecom,
                           feishu_webhook=args.feishu)
        if not results:
            print("⚠  未配置任何推送渠道（设置 WECOM_WEBHOOK_URL / FEISHU_WEBHOOK_URL）")
        for ch, (ok, msg) in results.items():
            print(f"  {ch}: {'✓' if ok else '✗'} {msg}")
    else:
        print("已跳过推送（--no-push）")


if __name__ == "__main__":
    main()