from src.reporting import generate_markdown_report


def _cfg():
    return {
        "risk": {"stop_loss_pct": 0.08, "trailing_stop_pct": 0.10,
                 "take_profit_pct": 0.20, "single_stock_max": 0.15,
                 "total_position_max": 0.90},
    }


def _result():
    return {
        "position": 0.6,
        "picks": ["600000.XSHG", "600519.XSHG"],
        "weights": {"600000.XSHG": 0.3, "600519.XSHG": 0.3},
        "advice": {"caution": "建议仓位 60%"},
        "metrics": {"annualized_return": 0.12, "max_drawdown": 0.10,
                    "sharpe_ratio": 0.8},
    }


def test_report_contains_sections_and_values():
    md = generate_markdown_report(_result(), _cfg(), report_date="2026-08-10")
    assert "沪深量化操作建议 · 2026-08-10" in md
    assert "建议仓位" in md and "60%" in md
    assert "候选标的" in md
    assert "600000.XSHG" in md and "600519.XSHG" in md
    assert "风控纪律" in md and "-8%" in md
    assert "回测绩效参考" in md and "12.00%" in md
    assert "免责声明" in md


def test_report_empty_picks_shows_wait():
    result = _result()
    result["picks"] = []
    result["weights"] = {}
    md = generate_markdown_report(result, _cfg(), report_date="2026-08-10")
    assert "空仓观望" in md