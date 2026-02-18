import types

import pytest

from backend import stripe_utils
from backend.config import config


@pytest.fixture(autouse=True)
def mock_require_stripe(monkeypatch):
    monkeypatch.setattr(stripe_utils, "_require_stripe", lambda: None)


def test_choose_basic_price_id_supported_sizes(monkeypatch):
    monkeypatch.setattr(config, "stripe_price_id_basic_20", "price_20")
    monkeypatch.setattr(config, "stripe_price_id_basic_100", "price_100")
    monkeypatch.setattr(config, "stripe_price_id_basic_500", "price_500")
    monkeypatch.setattr(config, "stripe_price_id_basic_1000", "price_1000")
    assert stripe_utils.choose_basic_price_id(20) == "price_20"
    assert stripe_utils.choose_basic_price_id(100) == "price_100"
    assert stripe_utils.choose_basic_price_id(500) == "price_500"
    assert stripe_utils.choose_basic_price_id(1000) == "price_1000"


def test_choose_basic_price_id_fallback_20(monkeypatch):
    monkeypatch.setattr(config, "stripe_price_id_basic_20", None)
    monkeypatch.setattr(config, "stripe_price_id_basic", "basic_default")
    monkeypatch.setattr(config, "stripe_price_id", "legacy_default")
    assert stripe_utils.choose_basic_price_id(20) == "basic_default"


def test_choose_basic_price_id_unsupported(monkeypatch):
    monkeypatch.setattr(config, "stripe_price_id_basic_20", "price_20")
    with pytest.raises(Exception):
        stripe_utils.choose_basic_price_id(30)
