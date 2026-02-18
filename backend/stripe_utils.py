from typing import Any, Dict, Optional

from backend.config import config

try:  # pragma: no cover - optional dependency
    import stripe  # type: ignore
except ImportError:  # pragma: no cover
    stripe = None

try:
    from fastapi import HTTPException
except ImportError:  # pragma: no cover
    HTTPException = RuntimeError  # Fallback to a standard exception


def _require_stripe():
    if stripe is None:
        raise (
            HTTPException(status_code=500, detail="stripe package is required for payment operations")
            if HTTPException is not RuntimeError
            else RuntimeError("stripe package is required for payment operations")
        )
    key = config.stripe_secret_key
    if (config.stripe_mode or "").lower() == "test":
        key = config.stripe_secret_key_test or key
    if not key:
        raise (
            HTTPException(status_code=500, detail="STRIPE_SECRET_KEY is not configured")
            if HTTPException is not RuntimeError
            else RuntimeError("STRIPE_SECRET_KEY is not configured")
        )
    stripe.api_key = key


def create_checkout_session(pack_id: str, price_id: Optional[str], success_url: str, cancel_url: str) -> Dict[str, Any]:
    """
    Create a Stripe Checkout Session for the given pack_id.
    """
    _require_stripe()
    price = price_id or config.stripe_price_id_basic or config.stripe_price_id
    if not price:
        raise (
            HTTPException(status_code=500, detail="Stripe price ID is not configured for this product")
            if HTTPException is not RuntimeError
            else RuntimeError("Stripe price ID is not configured for this product")
        )
    session = stripe.checkout.Session.create(
        mode="payment",
        line_items=[{"price": price, "quantity": 1}],
        success_url=success_url,
        cancel_url=cancel_url,
        metadata={"pack_id": pack_id},
        locale='en',
    )
    return {"url": session.url}


def choose_basic_price_id(limit: int) -> Optional[str]:
    """
    Resolve the Stripe price ID for a basic/raw pack based on lead count.
    Supported sizes: 20, 100, 500, 1000.
    Falls back to legacy STRIPE_PRICE_ID/STRIPE_PRICE_ID_BASIC for 20 if specific IDs are missing.
    Raises HTTPException on unsupported sizes.
    """
    size_to_price = {
        20: config.stripe_price_id_basic_20 or config.stripe_price_id_basic or config.stripe_price_id,
        100: config.stripe_price_id_basic_100,
        500: config.stripe_price_id_basic_500,
        1000: config.stripe_price_id_basic_1000,
    }
    if limit not in size_to_price:
        raise (
            HTTPException(status_code=400, detail="Unsupported lead pack size")
            if HTTPException is not RuntimeError
            else RuntimeError("Unsupported lead pack size")
        )
    return size_to_price[limit]


def verify_webhook_signature(payload: bytes, sig_header: str):
    """
    Verify Stripe webhook signature and return the event.
    """
    _require_stripe()
    return stripe.Webhook.construct_event(
        payload=payload,
        sig_header=sig_header,
        secret=config.stripe_webhook_secret,
    )
