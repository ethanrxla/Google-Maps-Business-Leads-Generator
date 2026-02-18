import sys
from pathlib import Path
from types import SimpleNamespace

import pytest
try:
    import yaml  # type: ignore
except ImportError:  # pragma: no cover
    yaml = None


ROOT = Path(__file__).parents[2]
HARVEST_ROOT = ROOT / "harvest"
SRC_DIR = HARVEST_ROOT / "src"

# Ensure harvest/src is on path for imports
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))


@pytest.fixture(scope="session")
def harvest_config():
    config_path = HARVEST_ROOT / "config.yaml"
    text = config_path.read_text()
    if yaml:
        return yaml.safe_load(text)
    # Minimal fallback parser: capture top-level keys only
    cfg = {}
    for line in text.splitlines():
        if line and not line.startswith("#") and not line.startswith(" "):
            key = line.split(":")[0].strip()
            if key:
                cfg[key] = {}
    return cfg


@pytest.fixture
def temp_output_dir(tmp_path):
    out_dir = tmp_path / "harvest_output"
    out_dir.mkdir(parents=True, exist_ok=True)
    return out_dir


@pytest.fixture
def mock_subprocess_run(monkeypatch):
    calls = []

    def _fake_run(cmd, capture_output=False, text=False, timeout=None, env=None):
        calls.append(
            SimpleNamespace(cmd=cmd, capture_output=capture_output, text=text, timeout=timeout, env=env)
        )
        # Minimal CompletedProcess-like object
        return SimpleNamespace(returncode=0, stdout="ok", stderr="")

    monkeypatch.setattr("subprocess.run", _fake_run)
    return calls


@pytest.fixture
def mock_integrations(monkeypatch):
    # Basic API mocks returning static data
    monkeypatch.setattr("integrations.hunter_io.verify_email", lambda email: {"status": "valid"})
    monkeypatch.setattr("integrations.linkedin_api.fetch_company_profile", lambda domain: {"domain": domain})
    monkeypatch.setattr("integrations.email_verification.verify", lambda email: True)
    return True
