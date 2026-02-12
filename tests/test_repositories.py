"""Tests for db/repositories.py -- no-row handling, validation, source enum.

These tests mock the Supabase client so they run without a live database.
"""

import pytest
from unittest.mock import MagicMock, patch

from db.repositories import (
    RepositoryError,
    VALID_SOURCES,
    _safe_first,
    _validate_candidate,
    create_batch_run,
    get_batch_run,
    get_candidate,
    get_candidates,
    insert_candidate,
    insert_candidates_batch,
    update_batch_run,
    update_candidate,
    delete_candidate,
    count_candidates,
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _mock_client():
    """Create a mock Supabase client with chainable table methods."""
    client = MagicMock()
    return client


def _mock_execute(data, count=None):
    """Build a mock execute() result."""
    result = MagicMock()
    result.data = data
    result.count = count
    return result


def _valid_candidate(**overrides):
    """Return a minimal valid candidate dict."""
    base = {
        "name": "Test Biz",
        "name_normalized": "test-biz",
        "source": "google_places",
    }
    base.update(overrides)
    return base


# ---------------------------------------------------------------------------
# _safe_first
# ---------------------------------------------------------------------------

class TestSafeFirst:
    def test_returns_first_element(self):
        assert _safe_first([{"id": "abc"}], "test") == {"id": "abc"}

    def test_raises_on_empty_list(self):
        with pytest.raises(RepositoryError, match="Insert returned no rows"):
            _safe_first([], "test context")

    def test_raises_on_none(self):
        with pytest.raises(RepositoryError):
            _safe_first(None, "test context")


# ---------------------------------------------------------------------------
# Candidate validation
# ---------------------------------------------------------------------------

class TestValidateCandidate:
    def test_valid_candidate_passes(self):
        _validate_candidate(_valid_candidate())  # no exception

    @pytest.mark.parametrize("missing_field", ["name", "name_normalized", "source"])
    def test_missing_required_field(self, missing_field):
        c = _valid_candidate()
        c[missing_field] = ""
        with pytest.raises(RepositoryError, match=f"missing required field: {missing_field}"):
            _validate_candidate(c)

    def test_missing_field_none(self):
        c = _valid_candidate(name=None)
        with pytest.raises(RepositoryError, match="missing required field: name"):
            _validate_candidate(c)

    @pytest.mark.parametrize("source", sorted(VALID_SOURCES))
    def test_all_valid_sources_accepted(self, source):
        _validate_candidate(_valid_candidate(source=source))  # no exception

    def test_invalid_source_rejected(self):
        with pytest.raises(RepositoryError, match="Invalid source"):
            _validate_candidate(_valid_candidate(source="twitter_scrape"))

    def test_source_enum_completeness(self):
        """Verify the enum matches the DB CHECK constraint."""
        expected = {"google_places", "theharvester", "manual", "serp", "html_scrape"}
        assert VALID_SOURCES == expected


# ---------------------------------------------------------------------------
# insert_candidate
# ---------------------------------------------------------------------------

class TestInsertCandidate:
    @patch("db.repositories.get_client")
    def test_success(self, mock_get_client):
        client = _mock_client()
        mock_get_client.return_value = client
        client.table.return_value.insert.return_value.execute.return_value = (
            _mock_execute([{"id": "uuid-1", "name": "Test Biz"}])
        )

        result = insert_candidate(_valid_candidate())
        assert result["id"] == "uuid-1"

    @patch("db.repositories.get_client")
    def test_empty_result_raises(self, mock_get_client):
        client = _mock_client()
        mock_get_client.return_value = client
        client.table.return_value.insert.return_value.execute.return_value = (
            _mock_execute([])
        )

        with pytest.raises(RepositoryError, match="Insert returned no rows"):
            insert_candidate(_valid_candidate())

    def test_validation_before_insert(self):
        """Invalid candidate should raise before hitting the DB."""
        with pytest.raises(RepositoryError, match="missing required field"):
            insert_candidate({"name": "No Source"})


# ---------------------------------------------------------------------------
# insert_candidates_batch
# ---------------------------------------------------------------------------

class TestInsertCandidatesBatch:
    def test_empty_list_returns_empty(self):
        assert insert_candidates_batch([]) == []

    @patch("db.repositories.get_client")
    def test_success(self, mock_get_client):
        client = _mock_client()
        mock_get_client.return_value = client
        rows = [{"id": "1"}, {"id": "2"}]
        client.table.return_value.insert.return_value.execute.return_value = (
            _mock_execute(rows)
        )

        result = insert_candidates_batch([_valid_candidate(), _valid_candidate(name="Biz 2")])
        assert len(result) == 2

    def test_invalid_candidate_in_batch_raises(self):
        candidates = [_valid_candidate(), {"name": "Bad", "name_normalized": "bad"}]
        with pytest.raises(RepositoryError, match="Candidate at index 1"):
            insert_candidates_batch(candidates)

    @patch("db.repositories.get_client")
    def test_empty_result_raises(self, mock_get_client):
        client = _mock_client()
        mock_get_client.return_value = client
        client.table.return_value.insert.return_value.execute.return_value = (
            _mock_execute([])
        )

        with pytest.raises(RepositoryError, match="Batch insert returned no rows"):
            insert_candidates_batch([_valid_candidate()])


# ---------------------------------------------------------------------------
# get_candidate / get_batch_run (no-row handling)
# ---------------------------------------------------------------------------

class TestGetNoRow:
    @patch("db.repositories.get_client")
    def test_get_candidate_returns_none_for_missing(self, mock_get_client):
        client = _mock_client()
        mock_get_client.return_value = client
        client.table.return_value.select.return_value.eq.return_value.maybe_single.return_value.execute.return_value = (
            _mock_execute(None)
        )

        assert get_candidate("nonexistent-id") is None

    @patch("db.repositories.get_client")
    def test_get_candidate_returns_row_when_found(self, mock_get_client):
        client = _mock_client()
        mock_get_client.return_value = client
        row = {"id": "uuid-1", "name": "Found"}
        client.table.return_value.select.return_value.eq.return_value.maybe_single.return_value.execute.return_value = (
            MagicMock(data=row)
        )

        assert get_candidate("uuid-1") == row

    @patch("db.repositories.get_client")
    def test_get_batch_run_returns_none_for_missing(self, mock_get_client):
        client = _mock_client()
        mock_get_client.return_value = client
        client.table.return_value.select.return_value.eq.return_value.maybe_single.return_value.execute.return_value = (
            _mock_execute(None)
        )

        assert get_batch_run("nonexistent-id") is None

    @patch("db.repositories.get_client")
    def test_get_candidates_returns_empty_list(self, mock_get_client):
        client = _mock_client()
        mock_get_client.return_value = client
        client.table.return_value.select.return_value.range.return_value.execute.return_value = (
            _mock_execute([])
        )

        result = get_candidates()
        assert result == []

    @patch("db.repositories.get_client")
    def test_get_candidates_returns_none_data_safely(self, mock_get_client):
        """If result.data is None (edge case), should return empty list."""
        client = _mock_client()
        mock_get_client.return_value = client
        client.table.return_value.select.return_value.range.return_value.execute.return_value = (
            _mock_execute(None)
        )

        result = get_candidates()
        assert result == []


# ---------------------------------------------------------------------------
# update_candidate / update_batch_run (no-row handling)
# ---------------------------------------------------------------------------

class TestUpdateNoRow:
    @patch("db.repositories.get_client")
    def test_update_candidate_returns_none_for_missing(self, mock_get_client):
        client = _mock_client()
        mock_get_client.return_value = client
        client.table.return_value.update.return_value.eq.return_value.execute.return_value = (
            _mock_execute([])
        )

        result = update_candidate("nonexistent", {"status": "deduped"})
        assert result is None

    @patch("db.repositories.get_client")
    def test_update_batch_run_returns_none_for_missing(self, mock_get_client):
        client = _mock_client()
        mock_get_client.return_value = client
        client.table.return_value.update.return_value.eq.return_value.execute.return_value = (
            _mock_execute([])
        )

        result = update_batch_run("nonexistent", {"status": "completed"})
        assert result is None


# ---------------------------------------------------------------------------
# delete_candidate
# ---------------------------------------------------------------------------

class TestDeleteCandidate:
    @patch("db.repositories.get_client")
    def test_delete_returns_true(self, mock_get_client):
        client = _mock_client()
        mock_get_client.return_value = client
        client.table.return_value.delete.return_value.eq.return_value.execute.return_value = (
            _mock_execute([{"id": "deleted"}])
        )

        assert delete_candidate("uuid-1") is True

    @patch("db.repositories.get_client")
    def test_delete_returns_false_for_missing(self, mock_get_client):
        client = _mock_client()
        mock_get_client.return_value = client
        client.table.return_value.delete.return_value.eq.return_value.execute.return_value = (
            _mock_execute([])
        )

        assert delete_candidate("nonexistent") is False


# ---------------------------------------------------------------------------
# count_candidates
# ---------------------------------------------------------------------------

class TestCountCandidates:
    @patch("db.repositories.get_client")
    def test_returns_count(self, mock_get_client):
        client = _mock_client()
        mock_get_client.return_value = client
        client.table.return_value.select.return_value.execute.return_value = (
            _mock_execute([], count=42)
        )

        assert count_candidates() == 42

    @patch("db.repositories.get_client")
    def test_returns_zero_when_none(self, mock_get_client):
        client = _mock_client()
        mock_get_client.return_value = client
        client.table.return_value.select.return_value.execute.return_value = (
            _mock_execute([], count=None)
        )

        assert count_candidates() == 0


# ---------------------------------------------------------------------------
# create_batch_run
# ---------------------------------------------------------------------------

class TestCreateBatchRun:
    @patch("db.repositories.get_client")
    def test_success(self, mock_get_client):
        client = _mock_client()
        mock_get_client.return_value = client
        client.table.return_value.insert.return_value.execute.return_value = (
            _mock_execute([{"id": "batch-1", "batch_type": "city_sweep"}])
        )

        result = create_batch_run("city_sweep", {"query": "dentists"})
        assert result["id"] == "batch-1"

    @patch("db.repositories.get_client")
    def test_empty_result_raises(self, mock_get_client):
        client = _mock_client()
        mock_get_client.return_value = client
        client.table.return_value.insert.return_value.execute.return_value = (
            _mock_execute([])
        )

        with pytest.raises(RepositoryError, match="batch_runs insert"):
            create_batch_run("city_sweep")
