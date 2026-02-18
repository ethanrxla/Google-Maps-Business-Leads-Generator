import hmac
import hashlib

from backend.coinbase_payments import verify_coinbase_webhook


def test_coinbase_webhook_verification(monkeypatch):
    secret = "secret"
    monkeypatch.setattr("backend.coinbase_payments.WEBHOOK_SECRET", secret)
    body = b'{"event":{"type":"charge:confirmed"}}'
    sig = hmac.new(secret.encode(), body, hashlib.sha256).hexdigest()
    headers = {"X-CC-Webhook-Signature": sig}
    event = verify_coinbase_webhook(headers, body)
    assert event and event["event"]["type"] == "charge:confirmed"


def test_coinbase_webhook_invalid_signature(monkeypatch):
    monkeypatch.setattr("backend.coinbase_payments.WEBHOOK_SECRET", "secret")
    body = b'{}'
    headers = {"X-CC-Webhook-Signature": "bad"}
    event = verify_coinbase_webhook(headers, body)
    assert event is None
