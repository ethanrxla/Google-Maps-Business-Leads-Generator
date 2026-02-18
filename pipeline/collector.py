"""Stage 1: Candidate collection from Google Places + enrichment sources.

Calls existing leadgen functions internally and produces candidate dicts
ready for Supabase insertion.
"""

import logging
from typing import Optional

from leadgen.analysis import analyze_html
from leadgen.email_extract import extract_emails
from leadgen.places import get_details, search_places
from leadgen.website_fetch import fetch_html
from pipeline.deduper import normalize_name

logger = logging.getLogger(__name__)


def _normalize_city(address: str | None) -> str | None:
    """Extract and normalize city from a formatted address.

    Google Places addresses typically look like:
      "123 Main St, Miami, FL 33101, USA"
    We try to grab the city component (second element in a 4-part address,
    or first element in a 2-part address).
    """
    if not address:
        return None
    parts = [p.strip() for p in address.split(",") if p.strip()]
    if not parts:
        return None
    # 4+ parts: "street, city, state+zip, country" -> city is parts[1]
    if len(parts) >= 4:
        city = parts[1].strip().lower()
        return city if city else None
    # 3 parts: "city, state, country" -> city is parts[0]
    if len(parts) == 3:
        city = parts[0].strip().lower()
        return city if city else None
    # 2 parts: "city, state" -> city is parts[0]
    if len(parts) == 2:
        city = parts[0].strip().lower()
        return city if city else None
    return parts[0].strip().lower() or None


def collect_candidates(
    query: str,
    limit: int = 50,
    batch_id: Optional[str] = None,
    source: str = "google_places",
) -> tuple[list[dict], str]:
    """Collect raw candidates from Google Places.

    Returns (candidates, api_status) where each candidate is a dict
    matching the Candidate dataclass fields.
    """
    businesses, api_status = search_places(query, limit=limit, include_status=True)

    candidates = []
    for biz in businesses:
        biz = get_details(biz)

        html = fetch_html(biz.website) if biz.website else None
        emails = extract_emails(html) if html else []

        if biz.email is None and emails:
            biz.email = emails[0]
            biz.email_source = "html"

        analysis = analyze_html(html)

        candidate = {
            "name": biz.name,
            "name_normalized": normalize_name(biz.name) if biz.name else "",
            "source": source,
            "address": biz.address,
            "city_normalized": _normalize_city(biz.address),
            "phone_raw": biz.phone,
            "email_raw": biz.email,
            "email_source": biz.email_source,
            "website": biz.website,
            "source_id": biz.place_id,
            "collection_batch_id": batch_id,
            "status": "new",
            # Analysis flags
            "has_website": analysis.has_website,
            "needs_website": analysis.needs_website,
            "needs_redesign": analysis.needs_redesign,
            "needs_chatbot": analysis.needs_chatbot,
            "needs_ai_integration": analysis.needs_ai_integration,
        }
        candidates.append(candidate)

    return candidates, api_status
