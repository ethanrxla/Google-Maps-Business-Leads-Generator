import os
import hmac
import hashlib
import json
from typing import Dict, Any, Optional

import requests

API_KEY = os.getenv("COINBASE_API_KEY")
WEBHOOK_SECRET = os.getenv("COINBASE_WEBHOOK_SECRET", "")
API_BASE = "https://api.commerce.coinbase.com"
API_VERSION = "2018-03-22"


def create_coinbase_charge(product_name: str, price_usd: float, metadata: Dict[str, Any]) -> Dict[str, Any]:
    headers = {
        "X-CC-Api-Key": API_KEY or "",
        "X-CC-Version": API_VERSION,
        "Content-Type": "application/json",
    }
    payload = {
        "name": product_name,
        "pricing_type": "fixed_price",
        "local_price": {"amount": str(price_usd), "currency": "USD"},
        "metadata": metadata,
    }
    resp = requests.post(f"{API_BASE}/charges", headers=headers, json=payload, timeout=10)
    if resp.status_code != 201:
        return {"error": resp.text, "status_code": resp.status_code}
    data = resp.json().get("data", {})
    return {"hosted_url": data.get("hosted_url"), "charge_id": data.get("id"), "raw": data}


def verify_coinbase_webhook(headers: Dict[str, str], body: bytes) -> Optional[Dict[str, Any]]:
    signature = headers.get("X-CC-Webhook-Signature") or headers.get("x-cc-webhook-signature")
    if not signature:
        return None
    computed = hmac.new(WEBHOOK_SECRET.encode(), body, hashlib.sha256).hexdigest()
    if not hmac.compare_digest(signature, computed):
        return None
    try:
        return json.loads(body.decode())
    except Exception:
        return None


def check_charge_status(charge_id: str) -> Dict[str, Any]:
    headers = {
        "X-CC-Api-Key": API_KEY or "",
        "X-CC-Version": API_VERSION,
        "Content-Type": "application/json",
    }
    resp = requests.get(f"{API_BASE}/charges/{charge_id}", headers=headers, timeout=10)
    if resp.status_code != 200:
        return {"error": resp.text, "status_code": resp.status_code}
    data = resp.json().get("data", {})
    timeline = data.get("timeline", [])
    status = data.get("status") or (timeline[-1].get("status") if timeline else "unknown")
    return {"status": status, "raw": data}
