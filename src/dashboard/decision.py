"""DSA 风格决策仪表盘。

将 quant-system 的端到端信号（大盘择时 position、选股评分 scores、
入选 picks、准入过滤 rejected）映射为「买入 / 观望 / 卖出」五星评级，
生成类似 daily_stock_analysis 的决策仪表盘 Markdown 文本。
"""

from src.reporting import generate_markdown_report


def _rating(site_default: bool, picked: bool, score: float) -> tuple[str, str]:
    """根据是否入选 + 评分，给出评级与一句话理由。

    返回 (评级, 简述)。评级∈{买入, 观望, 回避}。
    """
    if picked:
        return "买入", "入选组合，倾向积极"
    if score >= 0:
        return "观望", "通过准入但未入选"
    return "回避", "评分偏弱，暂不参与"


def build_decision_dashboard(result: dict, cfg: dict, report_date=None) -> str:
    """把流水线 result 渲染为决策仪表盘文本。"""
    from datetime import date
    report_date = report_date or date.today().isoformat()

    position = result.get("position", 0.0)
    picks = set(result.get("picks", []))
    scores = result.get("scores", {}) or {}
    rejected = result.get("rejected", {})

    # 汇总评级
    rated = []
    for code in scores:
        rating, note = _rating(True, code in picks, scores.get(code, 0.0))
        scored = f"{scores[code] * 100:+.2f}%" if scores.get(code) is not None else "n/a"
        rated.append((rating, code, scored, note))
    for code, reasons in rejected.items():
        rated.append(("回避", code, "n/a", "、".join(reasons)))

    # 统计
    counts = {"买入": 0, "观望": 0, "回避": 0}
    for r, *_ in rated:
        counts[r] = counts.get(r, 0) + 1

    lines = []
    lines.append(f"🎯 {report_date} 决策仪表盘")
    lines.append("")
    lines.append(f"共分析 {len(rated)} 只标的 | "
                 f"🟢买入:{counts.get('买入', 0)} "
                 f"🟡观望:{counts.get('观望', 0)} "
                 f"🔴回避:{counts.get('回避', 0)}")
    lines.append("")
    lines.append(f"📊 大盘择时建议仓位：**{position * 100:.0f}%**")
    lines.append("")
    lines.append("📈 标的一览")
    lines.append("")
    for rating, code, scored, note in rated:
        icon = {"买入": "🟢", "观望": "🟡", "回避": "🔴"}.get(rating, "⚪")
        lines.append(f"{icon} {code}: {rating} | 预测收益 {scored} | {note}")
    lines.append("")
    lines.append("📋 操作检查清单")
    lines.append("- 仓位 ≤ 择时建议；单票 ≤ 15%")
    lines.append("- 每只止损 -8%、止盈 +20%，触发即执行纪律")
    lines.append("- 行业分散 ≥ 5 只，单行业 ≤ 30%")
    lines.append("- 组合最大回撤 15% 强制清仓至现金")
    lines.append("")
    lines.append("---")
    lines.append("*决策由量化模型自动生成，仅供研究参考，不构成投资建议。*")
    return "\n".join(lines)


def build_full_report(result: dict, cfg: dict, report_date=None) -> str:
    """完整报告：决策仪表盘 + 详细 Markdown 报告。"""
    dashboard = build_decision_dashboard(result, cfg, report_date)
    detail = generate_markdown_report(result, cfg, report_date=report_date)
    return dashboard + "\n\n" + "=" * 60 + "\n\n" + detail