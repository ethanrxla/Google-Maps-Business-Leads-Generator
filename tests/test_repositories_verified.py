"""Tests for verified_leads CRUD in db/repositories.py.

Uses FakeTable/FakeQuery pattern to mock the Supabase client.
"""

import pytest

from db.repositories import (
    RepositoryError,
    count_verified_leads,
    get_verified_lead,
    get_verified_leads,
    insert_verified_lead,
    insert_verified_leads_batch,
    update_verified_lead,
)


# ---------------------------------------------------------------------------
# Fakes
# ---------------------------------------------------------------------------

class FakeResult:
    def __init__(self, data=None, count=None):
        self.data = data
        self.count = count


class FakeQuery:
    def __init__(self, rows=None, count=None):
        self._rows = rows if rows is not None else []
        self._count = count
        self._maybe_single = False

    def select(self, *args, **kwargs):
        return self

    def eq(self, col, val):
        return self

    def gte(self, col, val):
        return self

    def range(self, start, end):
        return self

    def limit(self, n):
        return self

    def maybe_single(self):
        self._maybe_single = True
        return self

    def execute(self):
        data = self._rows
        if self._maybe_single and isinstance(data, list):
            data = data[0] if data else None
        return FakeResult(data=data, count=self._count)


class FakeInsertQuery:
    def __init__(self, return_rows):
        self._return_rows = return_rows

    def execute(self):
        return FakeResult(data=self._return_rows)


class FakeUpdateQuery:
    def __init__(self, return_rows):
        self._return_rows = return_rows

    def eq(self, col, val):
        return self

    def execute(self):
        return FakeResult(data=self._return_rows)


class FakeTable:
    def __init__(self, insert_rows=None, query_rows=None, update_rows=None, count=None):
        self._insert_rows = insert_rows
        self._query_rows = query_rows or []
        self._update_rows = update_rows
        self._count = count

    def insert(self, data):
        return FakeInsertQuery(self._insert_rows)

    def select(self, *args, **kwargs):
        return FakeQuery(rows=self._query_rows, count=self._count)

    def update(self, data):
        return FakeUpdateQuery(self._update_rows or [])


class FakeClient:
    def __init__(self, table_map=None):
        self._table_map = table_map or {}

    def table(self, name):
        return self._table_map.get(name, FakeTable())


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------

class TestInsertVerifiedLead:
    def test_success(self, monkeypatch):
        row = {"id": "v1", "name": "Biz", "name_normalized": "biz"}
        client = FakeClient({"verified_leads": FakeTable(insert_rows=[row])})
        monkeypatch.setattr("db.repositories.get_client", lambda: client)

        result = insert_verified_lead({"name": "Biz", "name_normalized": "biz"})
        assert result["id"] == "v1"

    def test_missing_name(self):
        with pytest.raises(RepositoryError, match="name"):
            insert_verified_lead({"name_normalized": "biz"})

    def test_missing_name_normalized(self):
        with pytest.raises(RepositoryError, match="name_normalized"):
            insert_verified_lead({"name": "Biz"})


class TestInsertVerifiedLeadsBatch:
    def test_success(self, monkeypatch):
        rows = [
            {"id": "v1", "name": "A", "name_normalized": "a"},
            {"id": "v2", "name": "B", "name_normalized": "b"},
        ]
        client = FakeClient({"verified_leads": FakeTable(insert_rows=rows)})
        monkeypatch.setattr("db.repositories.get_client", lambda: client)

        result = insert_verified_leads_batch([
            {"name": "A", "name_normalized": "a"},
            {"name": "B", "name_normalized": "b"},
        ])
        assert len(result) == 2

    def test_empty_list(self, monkeypatch):
        assert insert_verified_leads_batch([]) == []

    def test_validation_error(self):
        with pytest.raises(RepositoryError, match="index 0"):
            insert_verified_leads_batch([{"name": "A"}])

    def test_no_rows_returned(self, monkeypatch):
        client = FakeClient({"verified_leads": FakeTable(insert_rows=[])})
        monkeypatch.setattr("db.repositories.get_client", lambda: client)
        with pytest.raises(RepositoryError, match="Batch insert"):
            insert_verified_leads_batch([{"name": "A", "name_normalized": "a"}])


class TestGetVerifiedLeads:
    def test_returns_rows(self, monkeypatch):
        rows = [{"id": "v1", "name": "A"}, {"id": "v2", "name": "B"}]
        client = FakeClient({"verified_leads": FakeTable(query_rows=rows)})
        monkeypatch.setattr("db.repositories.get_client", lambda: client)

        result = get_verified_leads(city="Miami")
        assert len(result) == 2

    def test_empty(self, monkeypatch):
        client = FakeClient({"verified_leads": FakeTable(query_rows=[])})
        monkeypatch.setattr("db.repositories.get_client", lambda: client)

        result = get_verified_leads()
        assert result == []


class TestGetVerifiedLead:
    def test_found(self, monkeypatch):
        row = {"id": "v1", "name": "A"}
        client = FakeClient({"verified_leads": FakeTable(query_rows=row)})
        monkeypatch.setattr("db.repositories.get_client", lambda: client)

        result = get_verified_lead("v1")
        assert result == row

    def test_not_found(self, monkeypatch):
        client = FakeClient({"verified_leads": FakeTable(query_rows=None)})
        monkeypatch.setattr("db.repositories.get_client", lambda: client)

        result = get_verified_lead("missing")
        assert result is None


class TestUpdateVerifiedLead:
    def test_success(self, monkeypatch):
        row = {"id": "v1", "name": "Updated"}
        client = FakeClient({"verified_leads": FakeTable(update_rows=[row])})
        monkeypatch.setattr("db.repositories.get_client", lambda: client)

        result = update_verified_lead("v1", {"name": "Updated"})
        assert result["name"] == "Updated"

    def test_not_found(self, monkeypatch):
        client = FakeClient({"verified_leads": FakeTable(update_rows=[])})
        monkeypatch.setattr("db.repositories.get_client", lambda: client)

        result = update_verified_lead("missing", {"name": "X"})
        assert result is None


class TestCountVerifiedLeads:
    def test_count(self, monkeypatch):
        client = FakeClient({"verified_leads": FakeTable(count=42)})
        monkeypatch.setattr("db.repositories.get_client", lambda: client)

        assert count_verified_leads(batch_id="b1") == 42

    def test_zero(self, monkeypatch):
        client = FakeClient({"verified_leads": FakeTable(count=0)})
        monkeypatch.setattr("db.repositories.get_client", lambda: client)

        assert count_verified_leads() == 0
