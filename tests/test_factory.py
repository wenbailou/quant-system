import pytest
from src.data.factory import get_loader
from src.data.loader import MockMarketDataLoader
from src.data.joinquant import JoinQuantDataLoader


def test_get_loader_mock():
    cfg = {"data": {"source": "mock", "start_date": "2020-01-01",
                    "end_date": "2020-01-10"}}
    loader = get_loader(cfg)
    assert isinstance(loader, MockMarketDataLoader)


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