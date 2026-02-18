from backend.coinbase_payments import check_charge_status


class DummyResponse:
    def __init__(self, status_code=200, json_data=None, text=""):
        self.status_code = status_code
        self._json = json_data or {}
        self.text = text

    def json(self):
        return self._json


def test_coinbase_check_status_success(monkeypatch):
    def fake_get(url, headers=None, timeout=None):
        return DummyResponse(200, {"data": {"status": "completed", "timeline": [{"status": "pending"}]}})

    monkeypatch.setattr("requests.get", fake_get)
    res = check_charge_status("charge_1")
    assert res["status"] == "completed"


def test_coinbase_check_status_failure(monkeypatch):
    def fake_get(url, headers=None, timeout=None):
        return DummyResponse(404, text="missing")

    monkeypatch.setattr("requests.get", fake_get)
    res = check_charge_status("charge_1")
    assert "error" in res
