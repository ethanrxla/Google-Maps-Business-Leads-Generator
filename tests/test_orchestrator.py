"""Tests for pipeline/orchestrator.py -- full pipeline orchestration.

All stages and repositories are mocked via monkeypatch.
"""

import os
import tempfile

import pytest

from pipeline.orchestrator import main, run_batch


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _fake_candidates(count=3):
    return [
        {
            "id": f"c{i}",
            "name": f"Biz {i}",
            "name_normalized": f"biz_{i}",
            "source": "google_places",
            "city": "Miami",
            "phone_raw": f"555-{i:04d}",
            "email_raw": f"info{i}@biz{i}.com",
            "website": f"https://biz{i}.com",
            "status": "new",
            "has_website": True,
            "needs_website": False,
            "needs_redesign": True,
            "needs_chatbot": True,
            "needs_ai_integration": True,
        }
        for i in range(count)
    ]


def _fake_verified(count=3):
    return [
        {
            "id": f"v{i}",
            "name": f"Biz {i}",
            "name_normalized": f"biz_{i}",
            "email": f"info{i}@biz{i}.com",
            "email_verified": True,
            "phone": f"555-{i:04d}",
            "website": f"https://biz{i}.com",
            "dedup_key": f"biz_{i}|555{i:04d}",
            "needs_score": 40,
            "lead_quality_score": 60,
            "data_freshness_days": 0,
        }
        for i in range(count)
    ]


def _fake_pack():
    return {
        "pack_id": "us_fl_miami_dentists_3",
        "niche": "dentists",
        "city": "Miami",
        "sellable": True,
        "quality_gate_failures": [],
        "lead_count": 3,
    }


def _setup_mocks(monkeypatch, candidates=None, verified=None, pack=None):
    """Wire up all mocks for a successful pipeline run."""
    candidates = candidates if candidates is not None else _fake_candidates()
    verified = verified if verified is not None else _fake_verified()
    pack = pack if pack is not None else _fake_pack()

    # Repos
    monkeypatch.setattr(
        "pipeline.orchestrator.create_batch_run",
        lambda *a, **kw: {"id": "batch-1", "status": "pending"},
    )
    monkeypatch.setattr(
        "pipeline.orchestrator.update_batch_run",
        lambda *a, **kw: {"id": "batch-1"},
    )
    monkeypatch.setattr(
        "pipeline.orchestrator.insert_candidates_batch",
        lambda c: c,
    )
    monkeypatch.setattr(
        "pipeline.orchestrator.insert_verified_leads_batch",
        lambda v: v,
    )
    monkeypatch.setattr(
        "pipeline.orchestrator.insert_pack",
        lambda p: p,
    )
    monkeypatch.setattr(
        "pipeline.orchestrator.insert_pack_entries_batch",
        lambda e: e,
    )

    events = []
    monkeypatch.setattr(
        "pipeline.orchestrator.log_pipeline_event",
        lambda batch_id, event_type, payload=None: events.append(
            {"batch_id": batch_id, "event_type": event_type, "payload": payload}
        ) or {"id": "e1"},
    )

    # Stages
    monkeypatch.setattr(
        "pipeline.orchestrator.collect_candidates",
        lambda **kw: (candidates, "OK"),
    )
    monkeypatch.setattr(
        "pipeline.orchestrator.dedupe_candidates",
        lambda c: (c, []),
    )
    monkeypatch.setattr(
        "pipeline.orchestrator.verify_candidates",
        lambda c, **kw: verified,
    )
    monkeypatch.setattr(
        "pipeline.orchestrator.assemble_pack",
        lambda **kw: pack,
    )

    return events


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------

class TestRunBatch:
    def test_successful_run(self, monkeypatch):
        events = _setup_mocks(monkeypatch)

        result = run_batch(
            batch_type="city_sweep",
            query="dentists Miami",
            city="Miami",
            state="FL",
            niche="dentists",
        )

        assert result["batch_id"] == "batch-1"
        assert result["status"] == "completed"
        assert result["candidates_collected"] == 3
        assert result["candidates_kept"] == 3
        assert result["verified_count"] == 3
        assert result["pack"]["sellable"] is True

    def test_pipeline_events_logged(self, monkeypatch):
        events = _setup_mocks(monkeypatch)

        run_batch(
            batch_type="city_sweep",
            query="dentists Miami",
            city="Miami",
        )

        event_types = [e["event_type"] for e in events]
        assert "collect_start" in event_types
        assert "collect_done" in event_types
        assert "dedupe_start" in event_types
        assert "dedupe_done" in event_types
        assert "verify_start" in event_types
        assert "verify_done" in event_types
        assert "assemble_start" in event_types
        assert "assemble_done" in event_types
        assert "pipeline_done" in event_types

    def test_zero_candidates(self, monkeypatch):
        events = _setup_mocks(monkeypatch, candidates=[])

        result = run_batch(
            batch_type="city_sweep",
            query="nonexistent",
            city="Nowhere",
        )

        assert result["status"] == "completed"
        assert result["candidates_collected"] == 0
        assert result["pack"] is None

    def test_error_handling(self, monkeypatch):
        events = _setup_mocks(monkeypatch)
        monkeypatch.setattr(
            "pipeline.orchestrator.collect_candidates",
            lambda **kw: (_ for _ in ()).throw(RuntimeError("API down")),
        )

        with pytest.raises(RuntimeError, match="API down"):
            run_batch(
                batch_type="city_sweep",
                query="dentists",
                city="Miami",
            )

        # Should have logged error event
        error_events = [e for e in events if e["event_type"] == "pipeline_error"]
        assert len(error_events) == 1
        assert "API down" in error_events[0]["payload"]["error"]

    def test_passes_enrichment_clients(self, monkeypatch):
        captured_kwargs = {}

        def mock_verify(candidates, **kwargs):
            captured_kwargs.update(kwargs)
            return _fake_verified()

        _setup_mocks(monkeypatch)
        monkeypatch.setattr("pipeline.orchestrator.verify_candidates", mock_verify)

        hunter = object()
        apollo = object()
        run_batch(
            batch_type="city_sweep",
            query="dentists",
            city="Miami",
            hunter_client=hunter,
            apollo_client=apollo,
        )

        assert captured_kwargs["hunter_client"] is hunter
        assert captured_kwargs["apollo_client"] is apollo


# ---------------------------------------------------------------------------
# CLI tests
# ---------------------------------------------------------------------------

class TestOrchestratorCLI:
    def test_cli_with_config(self, monkeypatch, tmp_path):
        """CLI loads YAML and calls run_batch with correct args."""
        cfg_file = tmp_path / "test_batch.yaml"
        cfg_file.write_text(
            "batch_type: city_sweep\n"
            "city: Miami\n"
            "state: FL\n"
            "niche: dentists\n"
            "query: 'dentists in Miami FL'\n"
            "limit: 25\n"
        )

        captured = {}

        def fake_run_batch(**kwargs):
            captured.update(kwargs)
            return {"batch_id": "b1", "status": "completed"}

        monkeypatch.setattr("pipeline.orchestrator.run_batch", fake_run_batch)

        ret = main(["--config", str(cfg_file)])

        assert ret == 0
        assert captured["batch_type"] == "city_sweep"
        assert captured["city"] == "Miami"
        assert captured["state"] == "FL"
        assert captured["niche"] == "dentists"
        assert captured["query"] == "dentists in Miami FL"
        assert captured["limit"] == 25

    def test_cli_missing_config(self):
        """Omitting --config should cause SystemExit (argparse error)."""
        with pytest.raises(SystemExit) as exc_info:
            main([])
        assert exc_info.value.code != 0

    def test_cli_query_fallback(self, monkeypatch, tmp_path):
        """When query is omitted, CLI builds one from niche + city + state."""
        cfg_file = tmp_path / "no_query.yaml"
        cfg_file.write_text(
            "batch_type: verify_pass\n"
            "city: Austin\n"
            "state: TX\n"
            "niche: plumbers\n"
        )

        captured = {}

        def fake_run_batch(**kwargs):
            captured.update(kwargs)
            return {"batch_id": "b2", "status": "completed"}

        monkeypatch.setattr("pipeline.orchestrator.run_batch", fake_run_batch)

        main(["--config", str(cfg_file)])

        assert captured["query"] == "plumbers in Austin TX"
