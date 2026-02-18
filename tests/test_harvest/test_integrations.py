import importlib


def test_integrations_importable():
    for name in ["integrations.hunter_io", "integrations.linkedin_api", "integrations.email_verification", "integrations.crm_connectors"]:
        mod = importlib.import_module(name)
        assert mod is not None
