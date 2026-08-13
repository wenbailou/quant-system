from src.dashboard.decision import build_decision_dashboard, build_full_report
from src.dashboard.notify import send_wecom, send_feishu, push_all


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
        "advice": {"caution": "建议仓位 30%"},
        "metrics": {},
    }


def test_decision_dashboard_contains_ratings():
    md = build_decision_dashboard(_result(), {"risk": {}}, report_date="2026-08-13")
    assert "决策仪表盘" in md
    assert "买入" in md
    assert "观望" in md
    assert "回避" in md
    assert "30%" in md


def test_full_report_contains_dashboard_and_detail():
    cfg = {"risk": {"stop_loss_pct": 0.08, "trailing_stop_pct": 0.10,
                    "take_profit_pct": 0.20, "single_stock_max": 0.15,
                    "total_position_max": 0.90}}
    md = build_full_report(_result(), cfg, report_date="2026-08-13")
    assert "决策仪表盘" in md
    assert "沪深量化操作建议" in md


def test_send_without_webhook_returns_fail():
    ok, msg = send_wecom("test", webhook=None)
    assert not ok
    assert "未配置" in msg
    ok2, msg2 = send_feishu("test", webhook=None)
    assert not ok2


def test_push_all_without_webhooks_empty():
    results = push_all("test", wecom_webhook=None, feishu_webhook=None)
    assert results == {}