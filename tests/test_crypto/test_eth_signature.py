from backend.crypto_auth import verify_signature, generate_nonce


def test_eth_signature_valid(monkeypatch):
    nonce = "abc"

    def fake_consume(wallet, chain, n):
        return n == nonce

    monkeypatch.setattr("backend.crypto_auth._consume_nonce", lambda a, b, c: fake_consume(a, b, c))
    monkeypatch.setattr("backend.crypto_auth._verify_eth_signature", lambda w, s, n: True)
    res = verify_signature("0xabc", "sig", nonce, "eth")
    assert res and res["chain"] == "eth"


def test_eth_signature_invalid(monkeypatch):
    monkeypatch.setattr("backend.crypto_auth._consume_nonce", lambda a, b, c: False)
    res = verify_signature("0xabc", "sig", "wrong", "eth")
    assert res is None
