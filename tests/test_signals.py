from src.signals import build_daily_advice


def test_build_daily_advice():
    advice = build_daily_advice(
        position=0.6,
        picks=["600001", "600002"],
        weights={"600001": 0.3, "600002": 0.3},
        caution="大盘中性，建议半仓",
    )
    assert advice["position"] == 0.6
    assert advice["picks"] == ["600001", "600002"]
    assert "caution" in advice