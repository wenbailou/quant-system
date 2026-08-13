"""决策仪表盘静态网页生成器。

将端到端流水线结果渲染为自包含 HTML（内嵌 CSS，无外部依赖），
便于部署到任意静态站点。每日定时刷新该页面即可。
"""

from datetime import date

from src.dashboard.decision import build_decision_dashboard


# 评级 → 颜色/图标
_RATING_COLOR = {
    "买入": "#d4edda",
    "观望": "#fff3cd",
    "回避": "#f8d7da",
}
_RATING_TEXT = {"买入": "#155724", "观望": "#856404", "回避": "#721c24"}
_RATING_ICON = {"买入": "🟢", "观望": "🟡", "回避": "🔴"}


def _html_escape(s: str) -> str:
    return (s.replace("&", "&amp;").replace("<", "&lt;")
             .replace(">", "&gt;").replace('"', "&quot;"))


def _build_ratings(result: dict) -> list[dict]:
    """从 result 提取评级行。"""
    picks = set(result.get("picks", []))
    scores = result.get("scores", {}) or {}
    rejected = result.get("rejected", {})
    rows = []
    for code in scores:
        picked = code in picks
        sc = scores.get(code)
        rating = "买入" if picked else ("观望" if (sc or 0) >= 0 else "回避")
        note = "入选组合，倾向积极" if picked else "通过准入但未入选"
        rows.append({
            "code": code, "rating": rating,
            "score": f"{sc * 100:+.2f}%" if sc is not None else "n/a",
            "note": note,
        })
    for code, reasons in rejected.items():
        rows.append({"code": code, "rating": "回避",
                     "score": "n/a", "note": "、".join(reasons)})
    return rows


def render_dashboard_html(result: dict, cfg: dict, report_date=None) -> str:
    """渲染决策仪表盘为自包含 HTML 页面。"""
    report_date = report_date or date.today().isoformat()
    position = result.get("position", 0.0)
    rows = _build_ratings(result)

    counts = {"买入": 0, "观望": 0, "回避": 0}
    for r in rows:
        counts[r["rating"]] = counts.get(r["rating"], 0) + 1

    # 评级行 HTML
    row_html = []
    for r in rows:
        color = _RATING_COLOR.get(r["rating"], "#e9ecef")
        text = _RATING_TEXT.get(r["rating"], "#212529")
        icon = _RATING_ICON.get(r["rating"], "⚪")
        row_html.append(
            f'<div class="row" style="background:{color};color:{text}">'
            f'<span class="icon">{icon}</span>'
            f'<span class="code">{_html_escape(r["code"])}</span>'
            f'<span class="rating">{r["rating"]}</span>'
            f'<span class="score">{r["score"]}</span>'
            f'<span class="note">{_html_escape(r["note"])}</span>'
            f'</div>'
        )
    rows_html = "\n".join(row_html) if row_html else (
        '<div class="row">暂无候选</div>'
    )

    return f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>沪深量化决策仪表盘 · {report_date}</title>
<style>
  * {{ box-sizing: border-box; margin: 0; padding: 0; }}
  body {{ font-family: "Segoe UI", "Microsoft YaHei", sans-serif;
         background: #f5f6fa; color: #2d3436; padding: 24px; }}
  .wrap {{ max-width: 860px; margin: 0 auto; }}
  h1 {{ font-size: 22px; margin-bottom: 4px; }}
  .date {{ color: #666; font-size: 13px; margin-bottom: 16px; }}
  .card {{ background: #fff; border-radius: 12px; padding: 20px;
          box-shadow: 0 2px 8px rgba(0,0,0,.06); margin-bottom: 16px; }}
  .summary {{ display: flex; gap: 16px; flex-wrap: wrap; }}
  .metric {{ flex: 1; min-width: 140px; text-align: center;
            padding: 12px; border-radius: 10px; background: #eef2ff; }}
  .metric .num {{ font-size: 26px; font-weight: 700; color: #4c6ef5; }}
  .metric .lbl {{ font-size: 12px; color: #666; margin-top: 4px; }}
  .chips {{ display: flex; gap: 12px; margin-top: 8px; }}
  .chip {{ padding: 4px 12px; border-radius: 20px; font-size: 13px; }}
  .chip.buy {{ background: #d4edda; color: #155724; }}
  .chip.watch {{ background: #fff3cd; color: #856404; }}
  .chip.avoid {{ background: #f8d7da; color: #721c24; }}
  .row {{ display: flex; align-items: center; gap: 12px;
         padding: 12px 14px; border-radius: 8px; margin-bottom: 8px; }}
  .row .icon {{ font-size: 18px; }}
  .row .code {{ font-weight: 600; width: 120px; }}
  .row .rating {{ width: 60px; font-weight: 700; }}
  .row .score {{ width: 90px; font-family: monospace; }}
  .row .note {{ flex: 1; font-size: 13px; opacity: .85; }}
  .checklist {{ list-style: none; }}
  .checklist li {{ padding: 6px 0; border-bottom: 1px dashed #eee;
                  font-size: 14px; }}
  .footer {{ text-align: center; color: #999; font-size: 12px;
            margin-top: 20px; }}
</style>
</head>
<body>
<div class="wrap">
  <h1>🎯 沪深量化决策仪表盘</h1>
  <div class="date">{report_date} · 仅供研究参考，不构成投资建议</div>

  <div class="card">
    <div class="summary">
      <div class="metric"><div class="num">{position * 100:.0f}%</div>
        <div class="lbl">建议仓位</div></div>
      <div class="metric"><div class="num">{counts.get("买入", 0)}</div>
        <div class="lbl">买入</div></div>
      <div class="metric"><div class="num">{counts.get("观望", 0)}</div>
        <div class="lbl">观望</div></div>
      <div class="metric"><div class="num">{counts.get("回避", 0)}</div>
        <div class="lbl">回避</div></div>
    </div>
    <div class="chips">
      <span class="chip buy">🟢 买入 {counts.get("买入", 0)}</span>
      <span class="chip watch">🟡 观望 {counts.get("观望", 0)}</span>
      <span class="chip avoid">🔴 回避 {counts.get("回避", 0)}</span>
    </div>
  </div>

  <div class="card">
    <h3>📈 标的一览</h3>
    <div style="margin-top:12px">
{rows_html}
    </div>
  </div>

  <div class="card">
    <h3>📋 操作检查清单</h3>
    <ul class="checklist">
      <li>仓位 ≤ 择时建议；单票 ≤ 15%</li>
      <li>每只止损 -8%、止盈 +20%，触发即执行纪律</li>
      <li>行业分散 ≥ 5 只，单行业 ≤ 30%</li>
      <li>组合最大回撤 15% 强制清仓至现金</li>
    </ul>
  </div>

  <div class="footer">决策由量化模型自动生成 · {report_date}</div>
</div>
</body>
</html>"""


def export_dashboard_html(
    cfg: dict,
    output_path: str | None = None,
    report_date=None,
    **pipeline_kwargs,
) -> str:
    """运行流水线并导出决策仪表盘静态 HTML。"""
    from src.pipeline import run_pipeline
    report_date = report_date or date.today().isoformat()
    result = run_pipeline(cfg, **pipeline_kwargs)
    html = render_dashboard_html(result, cfg, report_date=report_date)
    output_path = output_path or f"reports/dashboard_{report_date}.html"
    from pathlib import Path
    Path(output_path).parent.mkdir(parents=True, exist_ok=True)
    Path(output_path).write_text(html, encoding="utf-8")
    return str(output_path)