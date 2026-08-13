from src.dashboard.web import render_dashboard_html, _build_ratings


def _result():
    return {
        "position": 0.3,
        "picks": ["600000.XSHG", "600519.XSHG"],
        "weights": {"600000.XSHG": 0.15, "600519.XSHG": 0.15},
        "scores": {
            "600000.XSHG": 0.02,
            "600519.XSHG": -0.01,
            "600036.XSHG": 0.005,
        },
        "rejected": {"000001.XSHE": ["流动性不足"]},
    }


def test_render_dashboard_html_structure():
    html = render_dashboard_html(_result(), {}, report_date="2026-08-13")
    assert "<!DOCTYPE html>" in html
    assert "决策仪表盘" in html
    assert "建议仓位" in html
    assert "30%" in html
    assert "600000.XSHG" in html
    assert "买入" in html
    assert "回避" in html


def test_build_ratings_maps_picks_and_rejected():
    rows = _build_ratings(_result())
    ratings = {r["code"]: r["rating"] for r in rows}
    assert ratings["600000.XSHG"] == "买入"
    assert ratings["000001.XSHE"] == "回避"
    assert ratings["600036.XSHG"] == "观望"