"""Stage 3: Pack assembly from verified leads.

Takes a list of verified lead dicts, runs quality gates, computes
pack-level metrics, and returns a pack dict ready for persistence.
"""

import logging
from datetime import datetime, timedelta
from typing import Optional

from leadgen.generator import make_pack_id
from pipeline.quality_gates import check_quality_gates

logger = logging.getLogger(__name__)


def assemble_pack(
    leads: list[dict],
    niche: str,
    city: str,
    state: Optional[str] = None,
    country: str = "US",
    enrichment_tier: str = "basic",
    target_count: int = 0,
    max_freshness_days: int = 90,
    csv_path: Optional[str] = None,
    jsonl_path: Optional[str] = None,
) -> dict:
    """Assemble a pack from verified leads.

    Runs quality gates, computes metrics, and returns a pack dict.
    """
    pack_id = make_pack_id(
        country=country,
        state=state,
        county=None,
        city=city,
        niche=niche,
        limit=len(leads),
    )

    # Compute pack-level metrics
    lead_count = len(leads)
    emails = sum(1 for l in leads if l.get("email"))
    phones = sum(1 for l in leads if l.get("phone"))
    email_coverage = emails / lead_count if lead_count else 0.0
    phone_coverage = phones / lead_count if lead_count else 0.0

    quality_scores = [l.get("lead_quality_score", 0) for l in leads]
    needs_scores = [l.get("needs_score", 0) for l in leads]
    avg_quality = sum(quality_scores) / len(quality_scores) if quality_scores else 0.0
    avg_needs = sum(needs_scores) / len(needs_scores) if needs_scores else 0.0

    # Run quality gates
    enriched = enrichment_tier == "enriched"
    passed, failures = check_quality_gates(
        leads,
        target_count=target_count,
        enriched=enriched,
        max_freshness_days=max_freshness_days,
    )

    # Fail-closed: any failure reason forces sellable=false
    quality_gate_failures = sorted(str(r) for r in failures)
    sellable = passed and not quality_gate_failures

    now = datetime.now(tz=None)

    pack = {
        "pack_id": pack_id,
        "niche": niche,
        "city": city,
        "state": state,
        "country": country,
        "lead_count": lead_count,
        "enrichment_tier": enrichment_tier,
        "email_coverage": round(email_coverage, 4),
        "phone_coverage": round(phone_coverage, 4),
        "avg_lead_quality_score": round(avg_quality, 2),
        "avg_needs_score": round(avg_needs, 2),
        "sellable": sellable,
        "quality_gate_failures": quality_gate_failures,
        "assembled_at": now.isoformat(),
        "expires_at": (now + timedelta(days=90)).isoformat(),
        "csv_path": csv_path,
        "jsonl_path": jsonl_path,
    }

    return pack
