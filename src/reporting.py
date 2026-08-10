from datetime import date
from pathlib import Path

from src.pipeline import run_pipeline, run_walk_forward


def generate_markdown_report(result: dict, cfg: dict, report_date=None) -> str:
    """把端到端流水线结果渲染为每日下单信号 Markdown 报告。"""
    report_date = report_date or date.today().isoformat()
    position = result.get("position", 0.0)
    picks = result.get("picks", [])
    weights = result.get("weights", {})
    advice = result.get("advice", {"caution": ""})
    metrics = result.get("metrics", {})
    risk = cfg["risk"]

    lines = []
    lines.append(f"# 沪深量化操作建议 · {report_date}")
    lines.append("")
    lines.append(f"> 仅供研究参考，不构成投资建议 · 报告日期 {report_date}")
    lines.append("")

    lines.append("## 一、大盘择时")
    lines.append("")
    lines.append(f"- **建议仓位**：{position * 100:.0f}%")
    lines.append(f"- **择时提示**：{advice.get('caution', '')}")
    lines.append("")

    lines.append("## 二、候选标的（买入信号）")
    lines.append("")
    lines.append("| 代码 | 目标权重 | 操作 |")
    lines.append("|---|---|---|")
    total_weight = sum(weights.values())
    if picks and total_weight > 0:
        for code in picks:
            w = weights.get(code, 0.0)
            lines.append(f"| {code} | {w * 100:.1f}% | 买入 |")
    else:
        lines.append("| - | - | 空仓观望 |")
    lines.append("")

    lines.append("## 三、风控纪律")
    lines.append("")
    lines.append(f"- 单票止损：-{risk['stop_loss_pct'] * 100:.0f}%")
    lines.append(f"- 移动止损：自高点回撤 {risk['trailing_stop_pct'] * 100:.0f}%")
    lines.append(f"- 止盈：+{risk['take_profit_pct'] * 100:.0f}%")
    lines.append(f"- 单票仓位上限：{risk['single_stock_max'] * 100:.0f}%")
    lines.append(f"- 总仓位上限：{risk['total_position_max'] * 100:.0f}%")
    lines.append("")

    lines.append("## 四、回测绩效参考（walk-forward，无前视偏差）")
    lines.append("")
    lines.append(f"- 年化收益：{metrics.get('annualized_return', 0.0) * 100:.2f}%")
    lines.append(f"- 最大回撤：{metrics.get('max_drawdown', 0.0) * 100:.2f}%")
    lines.append(f"- 夏普比率：{metrics.get('sharpe_ratio', 0.0):.2f}")
    lines.append("")

    lines.append("---")
    lines.append("*免责声明：本报告由量化模型自动生成，回测收益不代表实盘收益，据此操作风险自负。*")
    lines.append("")
    return "\n".join(lines)


def export_daily_report(
    cfg: dict,
    output_path: str | Path | None = None,
    report_date=None,
    **pipeline_kwargs,
) -> str:
    """运行端到端流水线并导出每日下单信号 Markdown 报告。"""
    result = run_pipeline(cfg, **pipeline_kwargs)
    wf = run_walk_forward(cfg, **pipeline_kwargs)
    result["metrics"] = wf["metrics"]

    report_date = report_date or date.today().isoformat()
    md = generate_markdown_report(result, cfg, report_date=report_date)

    output_path = output_path or f"reports/daily_{report_date}.md"
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(md, encoding="utf-8")
    return str(output_path)