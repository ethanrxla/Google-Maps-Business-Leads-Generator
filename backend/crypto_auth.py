import json
import os
import sqlite3
import time
import uuid
from typing import Optional

# SQLite setup
DB_PATH = os.getenv("WALLET_AUTH_DB", "backend/wallet_auth.db")


def _conn():
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS wallet_nonces (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            wallet_address TEXT,
            chain TEXT,
            nonce TEXT,
            created_at REAL
        )
        """
    )
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS wallet_sessions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            wallet_address TEXT,
            chain TEXT,
            session_token TEXT,
            created_at REAL
        )
        """
    )
    return conn


def generate_nonce(wallet_address: str, chain: str) -> str:
    nonce = uuid.uuid4().hex
    conn = _conn()
    conn.execute(
        "INSERT INTO wallet_nonces (wallet_address, chain, nonce, created_at) VALUES (?, ?, ?, ?)",
        (wallet_address.lower(), chain.lower(), nonce, time.time()),
    )
    conn.commit()
    conn.close()
    return nonce


def _consume_nonce(wallet_address: str, chain: str, nonce: str) -> bool:
    conn = _conn()
    cur = conn.cursor()
    cur.execute(
        "SELECT id FROM wallet_nonces WHERE wallet_address=? AND chain=? AND nonce=?",
        (wallet_address.lower(), chain.lower(), nonce),
    )
    row = cur.fetchone()
    if not row:
        conn.close()
        return False
    cur.execute("DELETE FROM wallet_nonces WHERE id=?", (row[0],))
    conn.commit()
    conn.close()
    return True


def _store_session(wallet_address: str, chain: str) -> str:
    token = uuid.uuid4().hex
    conn = _conn()
    conn.execute(
        "INSERT INTO wallet_sessions (wallet_address, chain, session_token, created_at) VALUES (?, ?, ?, ?)",
        (wallet_address.lower(), chain.lower(), token, time.time()),
    )
    conn.commit()
    conn.close()
    return token


def _verify_eth_signature(wallet_address: str, signature: str, nonce: str) -> bool:
    # Placeholder verification; real ECDSA recovery can be added later
    return bool(signature and nonce and wallet_address)


def _verify_solana_signature(wallet_address: str, signature: str, nonce: str) -> bool:
    # Placeholder verification; real ed25519 verification can be added later
    return bool(signature and nonce and wallet_address)


def verify_signature(wallet_address: str, signature: str, nonce: str, chain: str) -> Optional[dict]:
    chain_l = chain.lower()
    if not _consume_nonce(wallet_address, chain_l, nonce):
        return None

    verified = False
    if chain_l == "eth":
        verified = _verify_eth_signature(wallet_address, signature, nonce)
    elif chain_l == "sol":
        verified = _verify_solana_signature(wallet_address, signature, nonce)
    else:
        verified = False

    if not verified:
        return None

    session_token = _store_session(wallet_address, chain_l)
    return {
        "user_id": wallet_address,
        "chain": chain_l,
        "session_token": session_token,
    }


def validate_session(session_token: str, wallet_address: str) -> bool:
    conn = _conn()
    cur = conn.cursor()
    cur.execute(
        "SELECT id FROM wallet_sessions WHERE session_token=? AND wallet_address=?",
        (session_token, wallet_address.lower()),
    )
    ok = cur.fetchone() is not None
    conn.close()
    return ok
