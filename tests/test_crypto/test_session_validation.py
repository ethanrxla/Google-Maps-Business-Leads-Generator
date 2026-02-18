from backend.crypto_auth import generate_nonce, verify_signature, validate_session


def test_session_validation(monkeypatch):
    # Stub verification
    monkeypatch.setattr("backend.crypto_auth._consume_nonce", lambda *a, **k: True)
    monkeypatch.setattr("backend.crypto_auth._verify_eth_signature", lambda *a, **k: True)

    nonce = generate_nonce("0xabc", "eth")
    session = verify_signature("0xabc", "sig", nonce, "eth")
    assert session is not None
    assert validate_session(session["session_token"], "0xabc") is True
