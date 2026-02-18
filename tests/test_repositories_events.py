"""Tests for pipeline_events CRUD in db/repositories.py.

Uses FakeTable/FakeQuery pattern to mock the Supabase client.
"""

import pytest

from db.repositories import (
    get_pipeline_events,
    log_pipeline_event,
)


# ---------------------------------------------------------------------------
# Fakes
# ---------------------------------------------------------------------------

class FakeResult:
    def __init__(self, data=None):
        self.data = data


class FakeQuery:
    def __init__(self, rows=None):
        self._rows = rows or []

    def select(self, *args, **kwargs):
        return self

    def eq(self, col, val):
        return self

    def limit(self, n):
        return self

    def execute(self):
        return FakeResult(data=self._rows)


class FakeInsertQuery:
    def __init__(self, return_rows):
        self._return_rows = return_rows

    def execute(self):
        return FakeResult(data=self._return_rows)


class FakeTable:
    def __init__(self, insert_rows=None, query_rows=None):
        self._insert_rows = insert_rows
        self._query_rows = query_rows or []

    def insert(self, data):
        return FakeInsertQuery(self._insert_rows)

    def select(self, *args, **kwargs):
        return FakeQuery(rows=self._query_rows)


class FakeClient:
    def __init__(self, table_map=None):
        self._table_map = table_map or {}

    def table(self, name):
        return self._table_map.get(name, FakeTable())


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------

class TestLogPipelineEvent:
    def test_success(self, monkeypatch):
        row = {"id": "e1", "batch_id": "b1", "event_type": "collect_start", "payload": {}}
        client = FakeClient({"pipeline_events": FakeTable(insert_rows=[row])})
        monkeypatch.setattr("db.repositories.get_client", lambda: client)

        result = log_pipeline_event("b1", "collect_start", {"count": 10})
        assert result["id"] == "e1"
        assert result["event_type"] == "collect_start"

    def test_default_payload(self, monkeypatch):
        row = {"id": "e2", "batch_id": "b1", "event_type": "done", "payload": {}}
        client = FakeClient({"pipeline_events": FakeTable(insert_rows=[row])})
        monkeypatch.setattr("db.repositories.get_client", lambda: client)

        result = log_pipeline_event("b1", "done")
        assert result["payload"] == {}


class TestGetPipelineEvents:
    def test_returns_events(self, monkeypatch):
        rows = [
            {"id": "e1", "batch_id": "b1", "event_type": "collect_start"},
            {"id": "e2", "batch_id": "b1", "event_type": "collect_done"},
        ]
        client = FakeClient({"pipeline_events": FakeTable(query_rows=rows)})
        monkeypatch.setattr("db.repositories.get_client", lambda: client)

        result = get_pipeline_events("b1")
        assert len(result) == 2

    def test_filter_by_event_type(self, monkeypatch):
        rows = [{"id": "e1", "batch_id": "b1", "event_type": "collect_start"}]
        client = FakeClient({"pipeline_events": FakeTable(query_rows=rows)})
        monkeypatch.setattr("db.repositories.get_client", lambda: client)

        result = get_pipeline_events("b1", event_type="collect_start")
        assert len(result) == 1

    def test_empty(self, monkeypatch):
        client = FakeClient({"pipeline_events": FakeTable(query_rows=[])})
        monkeypatch.setattr("db.repositories.get_client", lambda: client)

        assert get_pipeline_events("b1") == []
