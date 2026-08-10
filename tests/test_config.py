import pytest
from src.config import load_config


def test_load_config_returns_risk_params():
    cfg = load_config("config.yaml")
    assert cfg["risk"]["stop_loss_pct"] == 0.08
    assert cfg["risk"]["total_position_max"] == 0.90


def test_position_levels_mapping():
    cfg = load_config("config.yaml")
    assert cfg["position_levels"] == {
        "strong_bear": 0.0, "bear": 0.3, "neutral": 0.6, "bull": 0.9,
    }