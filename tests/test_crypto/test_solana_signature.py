from backend.crypto_auth import verify_signature


def test_solana_signature(monkeypatch):
    monkeypatch.setattr("backend.crypto_auth._consume_nonce", lambda a, b, c: True)
    monkeypatch.setattr("backend.crypto_auth._verify_solana_signature", lambda *a, **k: True)
    res = verify_signature("So111", "sig", "n", "sol")
    assert res and res["chain"] == "sol"
