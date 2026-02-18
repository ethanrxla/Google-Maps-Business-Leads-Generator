import time

import requests
from .config import config
from .models import Business

GOOGLE_PLACES_SEARCH = "https://maps.googleapis.com/maps/api/place/textsearch/json"
GOOGLE_PLACE_DETAILS = "https://maps.googleapis.com/maps/api/place/details/json"
RETRY_ATTEMPTS = 3
RETRY_DELAY_SEC = 0.1

# Pagination controls
PLACES_PAGE_SIZE = 20
MAX_PLACES_RESULTS = 1000
PLACES_NEXT_PAGE_SLEEP_S = 2.0


def _safe_json(resp):
    try:
        return resp.json() or {}
    except Exception:
        return {}


def _build_business(place: dict) -> Business | None:
    """
    Construct a Business from a Google Places result dict.
    Returns None if required fields are missing.
    """
    name = place.get("name")
    place_id = place.get("place_id")
    if not name or not place_id:
        return None

    return Business(
        name=name,
        address=place.get("formatted_address"),
        # We keep website if present; get_details() may refine later.
        website=place.get("website"),
        phone=place.get("formatted_phone_number") or place.get("international_phone_number"),
        email=place.get("email"),
        email_source="places" if place.get("email") else None,
        place_id=place_id,
    )


def _request_with_retry(url: str, params: dict, *, _sleep=time.sleep, _max_attempts: int = RETRY_ATTEMPTS):
    """
    Perform a requests.get with simple retry/backoff.
    Returns the Response on success, or None if all attempts fail.
    """
    last_exc = None
    for attempt in range(_max_attempts):
        try:
            return requests.get(url, params=params, timeout=10)
        except Exception as exc:
            last_exc = exc
            if attempt < _max_attempts - 1:
                _sleep(RETRY_DELAY_SEC)
    return None


def _normalize_result(value, include_status: bool):
    if include_status:
        return value
    return value[0]


def search_places(query: str, limit: int = 20, *, include_status: bool = False, _sleep=time.sleep, _max_attempts: int = RETRY_ATTEMPTS):
    """
    Fetch businesses from Google Places Text Search with pagination support.
    Respects `limit` (capped by MAX_PLACES_RESULTS) across multiple pages using next_page_token.
    """
    # Clamp limit to sane bounds
    effective_limit = limit or PLACES_PAGE_SIZE
    effective_limit = max(0, min(effective_limit, MAX_PLACES_RESULTS))

    collected = []
    next_page_token = None
    last_status = None

    while len(collected) < effective_limit:
        params = {"key": config.GOOGLE_API_KEY}
        if next_page_token:
            params["pagetoken"] = next_page_token
        else:
            params["query"] = query

        resp = _request_with_retry(GOOGLE_PLACES_SEARCH, params, _sleep=_sleep, _max_attempts=_max_attempts)
        if resp is None:
            last_status = last_status or "ERROR"
            break

        if resp.status_code != 200:
            last_status = f"HTTP_{resp.status_code}"
            break

        data = _safe_json(resp)
        status = data.get("status") or "ERROR"
        last_status = status

        if status not in ("OK", "ZERO_RESULTS"):
            # Stop on quota/errors; return what we have
            break

        page_results = data.get("results") or []
        for place in page_results:
            if len(collected) >= effective_limit:
                break
            business = _build_business(place)
            if business:
                collected.append(business)

        next_page_token = data.get("next_page_token")
        if not next_page_token or len(collected) >= effective_limit or status == "ZERO_RESULTS":
            break

        # Google requires a short delay before next_page_token becomes valid
        _sleep(PLACES_NEXT_PAGE_SLEEP_S)

    return _normalize_result((collected, last_status or "OK"), include_status)


def get_details(business: Business, *, _sleep=time.sleep, _max_attempts: int = RETRY_ATTEMPTS):
    if not business.place_id:
        return business

    params = {
        "place_id": business.place_id,
        "fields": "name,website,formatted_address,formatted_phone_number,international_phone_number",
        "key": config.GOOGLE_API_KEY
    }
    resp = _request_with_retry(GOOGLE_PLACE_DETAILS, params, _sleep=_sleep, _max_attempts=_max_attempts)
    if resp is None:
        return business

    if resp.status_code != 200:
        return business

    result = _safe_json(resp).get("result", {}) or {}

    if result.get("website") is not None:
        business.website = result.get("website")
    if result.get("formatted_address") is not None:
        business.address = result.get("formatted_address")
    if result.get("formatted_phone_number") is not None:
        business.phone = result.get("formatted_phone_number")
    elif result.get("international_phone_number") is not None:
        business.phone = result.get("international_phone_number")
    if result.get("email") is not None and business.email is None:
        business.email = result.get("email")
        business.email_source = "places"
    return business
