from pathlib import Path
import importlib

try:
    import yaml  # type: ignore
except ImportError:  # pragma: no cover
    yaml = None


def test_config_yaml_loads():
    config_path = Path(__file__).parents[2] / "harvest" / "config.yaml"
    text = config_path.read_text()
    if yaml:
        cfg = yaml.safe_load(text)
    else:
        cfg = {}
        for line in text.splitlines():
            if line and not line.startswith("#") and not line.startswith(" "):
                key = line.split(":")[0].strip()
                if key:
                    cfg[key] = {}
    assert "lead_harvesting" in cfg
    assert "theharvester" in cfg
    assert "export" in cfg


def test_directory_structure_exists():
    base = Path(__file__).parents[2] / "harvest" / "src" / "data"
    assert (base / "inputs").exists()
    assert (base / "outputs").exists()


def test_core_modules_importable():
    modules = [
        "core.lead_harvester",
        "core.wsl_harvester",
        "core.data_enricher",
        "core.contact_analyzer",
        "core.export_manager",
    ]
    for mod in modules:
        importlib.import_module(mod)
