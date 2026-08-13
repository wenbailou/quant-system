import pytest
from src.data.factory import get_loader
from src.data.loader import MockMarketDataLoader
from src.data.joinquant import JoinQuantDataLoader
from src.data.tickflow import TickFlowDataLoader


def test_get_loader_mock():
    cfg = {"data": {"source": "mock", "start_date": "2020-01-01",
                    "end_date": "2020-01-10"}}
    loader = get_loader(cfg)
    assert isinstance(loader, MockMarketDataLoader)


def test_get_loader_tickflow():
    cfg = {"data": {"source": "tickflow", "start_date": "2020-01-01",
                    "end_date": "2020-01-10", "tickflow": {"api_key": "k"}}}
    loader = get_loader(cfg)
    assert isinstance(loader, TickFlowDataLoader)
    assert loader._api_key == "k"


def test_get_loader_joinquant():
    cfg = {"data": {"source": "joinquant", "start_date": "2020-01-01",
                    "end_date": "2020-01-10",
                    "joinquant": {"account": "a", "password": "p"}}}
    loader = get_loader(cfg)
    assert isinstance(loader, JoinQuantDataLoader)


def test_get_loader_defaults_to_mock():
    cfg = {"data": {"start_date": "2020-01-01", "end_date": "2020-01-10"}}
    loader = get_loader(cfg)
    assert isinstance(loader, MockMarketDataLoader)


def test_get_loader_unknown_source_raises():
    cfg = {"data": {"source": "unknown"}}
    with pytest.raises(ValueError):
        get_loader(cfg)


def test_get_loader_joinquant_reads_env(monkeypatch):
    monkeypatch.setenv("JQ_ACCOUNT", "env_acc")
    monkeypatch.setenv("JQ_PASSWORD", "env_pwd")
    cfg = {"data": {"source": "joinquant", "start_date": "2020-01-01",
                    "end_date": "2020-01-10", "joinquant": {}}}
    loader = get_loader(cfg)
    assert loader.account == "env_acc"
    assert loader.password == "env_pwd"