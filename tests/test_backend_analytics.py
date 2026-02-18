def test_post_analytics_event_returns_200_ok(monkeypatch):
    from backend import server
    from fastapi.testclient import TestClient

    # This test will fail if the endpoint signature is wrong, as TestClient
    # correctly simulates the FastAPI dependency injection failure.
    def _fake_record_event(event, request):
        assert event.event_name == "test_event"
        assert request is not None
        return True

    monkeypatch.setattr(server, "_record_event", _fake_record_event)
    client = TestClient(server.app)

    payload = {"event_name": "test_event", "session_id": "test_session_123"}
    resp = client.post("/analytics/event", json=payload)
    assert resp.status_code == 200
    assert resp.json() == {"status": "ok"}