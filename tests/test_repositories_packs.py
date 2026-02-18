"""Tests for packs + pack_entries CRUD in db/repositories.py.

Uses FakeTable/FakeQuery pattern to mock the Supabase client.
"""

import pytest

from db.repositories import (
    RepositoryError,
    get_pack,
    get_pack_entries,
    get_sellable_packs,
    insert_pack,
    insert_pack_entries_batch,
    update_pack,
)


# ---------------------------------------------------------------------------
# Fakes (same pattern as test_repositories_verified.py)
# ---------------------------------------------------------------------------

class FakeResult:
    def __init__(self, data=None, count=None):
        self.data = data
        self.count = count


class FakeQuery:
    def __init__(self, rows=None):
        self._rows = rows if rows is not None else []
        self._maybe_single = False

    def select(self, *args, **kwargs):
        return self

    def eq(self, col, val):
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
        return FakeResult(data=data)


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
    def __init__(self, insert_rows=None, query_rows=None, update_rows=None):
        self._insert_rows = insert_rows
        self._query_rows = query_rows or []
        self._update_rows = update_rows

    def insert(self, data):
        return FakeInsertQuery(self._insert_rows)

    def select(self, *args, **kwargs):
        return FakeQuery(rows=self._query_rows)

    def update(self, data):
        return FakeUpdateQuery(self._update_rows or [])


class FakeClient:
    def __init__(self, table_map=None):
        self._table_map = table_map or {}

    def table(self, name):
        return self._table_map.get(name, FakeTable())


# ---------------------------------------------------------------------------
# Pack tests
# ---------------------------------------------------------------------------

class TestInsertPack:
    def test_success(self, monkeypatch):
        row = {"pack_id": "p1", "niche": "dentists", "city": "Miami"}
        client = FakeClient({"packs": FakeTable(insert_rows=[row])})
        monkeypatch.setattr("db.repositories.get_client", lambda: client)

        result = insert_pack({"pack_id": "p1", "niche": "dentists", "city": "Miami"})
        assert result["pack_id"] == "p1"

    def test_missing_pack_id(self):
        with pytest.raises(RepositoryError, match="pack_id"):
            insert_pack({"niche": "dentists"})


class TestGetPack:
    def test_found(self, monkeypatch):
        row = {"pack_id": "p1", "niche": "dentists"}
        client = FakeClient({"packs": FakeTable(query_rows=row)})
        monkeypatch.setattr("db.repositories.get_client", lambda: client)

        result = get_pack("p1")
        assert result == row

    def test_not_found(self, monkeypatch):
        client = FakeClient({"packs": FakeTable(query_rows=None)})
        monkeypatch.setattr("db.repositories.get_client", lambda: client)

        assert get_pack("missing") is None


class TestGetSellablePacks:
    def test_returns_rows(self, monkeypatch):
        rows = [{"pack_id": "p1", "sellable": True}]
        client = FakeClient({"packs": FakeTable(query_rows=rows)})
        monkeypatch.setattr("db.repositories.get_client", lambda: client)

        result = get_sellable_packs()
        assert len(result) == 1

    def test_empty(self, monkeypatch):
        client = FakeClient({"packs": FakeTable(query_rows=[])})
        monkeypatch.setattr("db.repositories.get_client", lambda: client)

        assert get_sellable_packs() == []


class TestUpdatePack:
    def test_success(self, monkeypatch):
        row = {"pack_id": "p1", "sellable": True}
        client = FakeClient({"packs": FakeTable(update_rows=[row])})
        monkeypatch.setattr("db.repositories.get_client", lambda: client)

        result = update_pack("p1", {"sellable": True})
        assert result["sellable"] is True

    def test_not_found(self, monkeypatch):
        client = FakeClient({"packs": FakeTable(update_rows=[])})
        monkeypatch.setattr("db.repositories.get_client", lambda: client)

        assert update_pack("missing", {"sellable": True}) is None


# ---------------------------------------------------------------------------
# Pack entries tests
# ---------------------------------------------------------------------------

class TestInsertPackEntriesBatch:
    def test_success(self, monkeypatch):
        rows = [{"pack_id": "p1", "lead_id": "v1"}]
        client = FakeClient({"pack_entries": FakeTable(insert_rows=rows)})
        monkeypatch.setattr("db.repositories.get_client", lambda: client)

        result = insert_pack_entries_batch([{"pack_id": "p1", "lead_id": "v1"}])
        assert len(result) == 1

    def test_empty(self, monkeypatch):
        assert insert_pack_entries_batch([]) == []

    def test_no_rows_returned(self, monkeypatch):
        client = FakeClient({"pack_entries": FakeTable(insert_rows=[])})
        monkeypatch.setattr("db.repositories.get_client", lambda: client)
        with pytest.raises(RepositoryError, match="Batch insert"):
            insert_pack_entries_batch([{"pack_id": "p1", "lead_id": "v1"}])


class TestGetPackEntries:
    def test_returns_entries(self, monkeypatch):
        rows = [{"pack_id": "p1", "lead_id": "v1"}, {"pack_id": "p1", "lead_id": "v2"}]
        client = FakeClient({"pack_entries": FakeTable(query_rows=rows)})
        monkeypatch.setattr("db.repositories.get_client", lambda: client)

        result = get_pack_entries("p1")
        assert len(result) == 2

    def test_empty(self, monkeypatch):
        client = FakeClient({"pack_entries": FakeTable(query_rows=[])})
        monkeypatch.setattr("db.repositories.get_client", lambda: client)

        assert get_pack_entries("p1") == []
