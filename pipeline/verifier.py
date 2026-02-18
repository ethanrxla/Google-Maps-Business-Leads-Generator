"""Stage 2: Candidate verification + confidence scoring.

Converts deduped candidates into verified leads by running them through
Hunter/Apollo enrichment and computing confidence/quality scores.
"""

import logging
from typing import Optional

from leadgen.ai_scoring import lead_quality_score, score_lead
from leadgen.enrichment import LeadEnricher
from leadgen.models import Business, LeadResult, WebsiteAnalysis
from pipeline.email_validator import compute_email_confidence

logger = logging.getLogger(__name__)


def _candidate_to_lead_result(candidate: dict) -> LeadResult:
    """Convert a candidate dict to a LeadResult for enrichment."""
    business = Business(
        name=candidate.get("name", ""),
        address=candidate.get("address"),
        website=candidate.get("website"),
        phone=candidate.get("phone_raw") or candidate.get("phone"),
        email=candidate.get("email_raw") or candidate.get("email"),
        email_source=candidate.get("email_source"),
        place_id=candidate.get("source_id"),
    )
    analysis = WebsiteAnalysis(
        has_website=candidate.get("has_website", False),
        needs_website=candidate.get("needs_website", False),
        needs_redesign=candidate.get("needs_redesign", False),
        needs_chatbot=candidate.get("needs_chatbot", False),
        needs_ai_integration=candidate.get("needs_ai_integration", False),
        raw_data={},
    )
    return LeadResult(business=business, analysis=analysis)


def verify_candidates(
    candidates: list[dict],
    hunter_client=None,
    apollo_client=None,
    batch_id: Optional[str] = None,
) -> list[dict]:
    """Verify and enrich a list of candidate dicts.

    Returns a list of verified lead dicts ready for insert into verified_leads.
    """
    enricher = LeadEnricher(
        apollo_client=apollo_client,
        hunter_client=hunter_client,
    )

    verified = []
    for candidate in candidates:
        lead = _candidate_to_lead_result(candidate)

        try:
            enricher.enrich_lead(lead)
        except Exception:
            logger.warning("Enrichment failed for %s", candidate.get("name", "?"))

        # Extract enrichment data for confidence scoring
        enrichment = lead.enrichment or {}
        hunter_data = enrichment.get("hunter", {})
        apollo_data = enrichment.get("apollo", {})

        hunter_result = hunter_data.get("result")
        hunter_score = hunter_data.get("score")
        apollo_confidence = apollo_data.get("confidence")

        email_conf = compute_email_confidence(
            hunter_result=hunter_result,
            hunter_score=hunter_score,
            apollo_confidence=apollo_confidence,
            source=lead.business.email_source,
        )

        needs = score_lead(lead)
        quality = lead_quality_score({
            "email": lead.business.email,
            "email_verified": hunter_result == "deliverable",
            "email_confidence": email_conf,
            "phone": lead.business.phone,
            "phone_verified": False,
            "website": lead.business.website,
            "website_alive": lead.analysis.has_website,
            "org_name": lead.org_name,
            "org_industry": lead.org_industry,
            "linkedin_url": lead.org_linkedin_url,
            "org_employee_count": lead.org_employee_count,
            "needs_score": needs,
        })

        # Build verification sources list
        verification_sources = []
        if hunter_data:
            verification_sources.append("hunter")
        if apollo_data:
            verification_sources.append("apollo")

        # Build provenance
        provenance = {}
        if hunter_data:
            provenance["hunter"] = {
                k: v for k, v in hunter_data.items()
                if k in ("result", "score", "status")
            }
        if apollo_data:
            provenance["apollo"] = {
                k: v for k, v in apollo_data.items()
                if k in ("confidence", "person", "organization")
            }

        # Extract org data from apollo
        org = apollo_data.get("organization", {}) or {}

        verified_lead = {
            "name": candidate.get("name", ""),
            "name_normalized": candidate.get("name_normalized", ""),
            "candidate_ids": [candidate["id"]] if candidate.get("id") else [],
            # Location
            "address": candidate.get("address"),
            "city": candidate.get("city") or candidate.get("city_normalized"),
            "state": candidate.get("state"),
            "country": candidate.get("country", "US"),
            # Contact
            "phone": lead.business.phone,
            "email": lead.business.email,
            "email_verified": hunter_result == "deliverable",
            "email_confidence": email_conf,
            "email_source": lead.business.email_source,
            "website": lead.business.website,
            "website_alive": lead.analysis.has_website,
            # Social
            "linkedin_url": lead.org_linkedin_url,
            # Enrichment
            "org_name": lead.org_name or org.get("name"),
            "org_industry": lead.org_industry or org.get("industry"),
            "org_employee_count": lead.org_employee_count or org.get("employee_count"),
            # Scoring
            "needs_score": needs,
            "lead_quality_score": quality,
            # Analysis flags
            "has_website": lead.analysis.has_website,
            "needs_website": lead.analysis.needs_website,
            "needs_redesign": lead.analysis.needs_redesign,
            "needs_chatbot": lead.analysis.needs_chatbot,
            "needs_ai_integration": lead.analysis.needs_ai_integration,
            # Metadata
            "verification_batch_id": batch_id,
            "verification_sources": verification_sources,
            "provenance": provenance,
            "data_freshness_days": 0,
            "dedup_key": candidate.get("dedup_key"),
        }

        verified.append(verified_lead)

    return verified
