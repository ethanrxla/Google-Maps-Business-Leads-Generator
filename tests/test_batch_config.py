"""Tests for pipeline/batch_config.py -- YAML batch config loader."""

import pytest

from pipeline.batch_config import BatchConfig, VALID_BATCH_TYPES, load_batch_config


class TestBatchConfig:
    def test_valid_city_sweep(self):
        cfg = BatchConfig(batch_type="city_sweep", city="Miami", state="FL")
        assert cfg.batch_type == "city_sweep"
        assert cfg.city == "Miami"
        assert cfg.country == "US"
        assert cfg.limit == 50

    def test_invalid_batch_type(self):
        with pytest.raises(ValueError, match="Invalid batch_type"):
            BatchConfig(batch_type="unknown", city="Miami")

    def test_missing_city(self):
        with pytest.raises(ValueError, match="city is required"):
            BatchConfig(batch_type="city_sweep", city="")

    def test_all_valid_batch_types(self):
        for bt in VALID_BATCH_TYPES:
            cfg = BatchConfig(batch_type=bt, city="X")
            assert cfg.batch_type == bt

    def test_defaults(self):
        cfg = BatchConfig(batch_type="city_sweep", city="Miami")
        assert cfg.enrichment_tier == "basic"
        assert cfg.sources == ["google_places"]
        assert cfg.max_freshness_days == 90
        assert cfg.niche is None
        assert cfg.query is None


class TestLoadBatchConfig:
    def test_load_valid(self, tmp_path):
        cfg_file = tmp_path / "batch.yaml"
        cfg_file.write_text(
            "batch_type: city_sweep\n"
            "city: Miami\n"
            "state: FL\n"
            "niche: dentists\n"
            "query: dentists in Miami FL\n"
            "limit: 100\n"
        )
        cfg = load_batch_config(str(cfg_file))
        assert cfg.batch_type == "city_sweep"
        assert cfg.city == "Miami"
        assert cfg.niche == "dentists"
        assert cfg.limit == 100

    def test_load_minimal(self, tmp_path):
        cfg_file = tmp_path / "batch.yaml"
        cfg_file.write_text("batch_type: verify_pass\ncity: Tampa\n")
        cfg = load_batch_config(str(cfg_file))
        assert cfg.batch_type == "verify_pass"
        assert cfg.enrichment_tier == "basic"

    def test_load_missing_file(self):
        with pytest.raises(FileNotFoundError):
            load_batch_config("/nonexistent/batch.yaml")

    def test_load_invalid_yaml(self, tmp_path):
        cfg_file = tmp_path / "batch.yaml"
        cfg_file.write_text("just a string")
        with pytest.raises(ValueError, match="expected a YAML mapping"):
            load_batch_config(str(cfg_file))

    def test_load_invalid_batch_type(self, tmp_path):
        cfg_file = tmp_path / "batch.yaml"
        cfg_file.write_text("batch_type: bogus\ncity: Miami\n")
        with pytest.raises(ValueError, match="Invalid batch_type"):
            load_batch_config(str(cfg_file))
