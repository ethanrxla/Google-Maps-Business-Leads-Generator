import importlib
import sys


def test_stripe_importable(monkeypatch):
    monkeypatch.setitem(sys.modules, "stripe", importlib.import_module("types"))
    mod = importlib.reload(importlib.import_module("backend.server"))
    assert mod is not None


def test_stripe_config_keys(monkeypatch):
    monkeypatch.setenv("STRIPE_SECRET_KEY", "sk_test_dummy")
    import backend.config as cfg

    # reload to pick env change
    import importlib
    importlib.reload(cfg)
    assert cfg.config.stripe_secret_key == "sk_test_dummy"
