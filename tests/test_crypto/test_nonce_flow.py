from backend.crypto_auth import generate_nonce, verify_signature


def test_nonce_flow(monkeypatch):
    # ensure consume nonce sees the generated value
    seen = {}

    def fake_consume(a, b, c):
        seen["nonce"] = c
        return True

    monkeypatch.setattr("backend.crypto_auth._consume_nonce", fake_consume)
    monkeypatch.setattr("backend.crypto_auth._verify_eth_signature", lambda *a, **k: True)
    nonce = generate_nonce("0xabc", "eth")
    res = verify_signature("0xabc", "sig", nonce, "eth")
    assert res and seen["nonce"] == nonce
