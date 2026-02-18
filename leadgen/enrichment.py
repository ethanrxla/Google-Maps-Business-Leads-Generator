import logging
from typing import Any, Dict, Optional
from urllib.parse import urlparse

from leadgen.models import LeadResult

logger = logging.getLogger(__name__)


def is_enrichment_error(data) -> bool:
    """Detect API error responses that should not be stored as valid enrichment.

    Catches: _safe_call {"error": ...} dicts, BuiltWith API error payloads,
    None, empty dicts, and non-dict types.
    """
    if data is None or not isinstance(data, dict) or not data:
        return True
    if "error" in data:
        return True
    if "Errors" in data:
        return True
    # BuiltWith "API Credits: 0" can appear in various response shapes
    for v in data.values():
        if isinstance(v, str) and "api credits" in v.lower():
            return True
    return False


def _extract_domain(url: Optional[str]) -> Optional[str]:
    if not url:
        return None
    parsed = urlparse(url if "://" in url else f"http://{url}")
    domain = parsed.netloc or parsed.path
    domain = domain.lstrip("www.")
    return domain or None


class LeadEnricher:
    """
    Orchestrates Apollo + Hunter enrichment for a single LeadResult.
    Keeps the original lead intact when clients are unavailable or errors occur.
    """

    def __init__(self, apollo_client=None, hunter_client=None):
        self.apollo = apollo_client
        self.hunter = hunter_client

    def _safe_call(self, fn, *args, **kwargs) -> Optional[Dict[str, Any]]:
        if not fn:
            return None
        try:
            result = fn(*args, **kwargs)
            if isinstance(result, dict) and result.get("rate_limited"):
                logger.warning("Enrichment rate-limited: %s", result)
                return result
            if is_enrichment_error(result):
                logger.warning("Enrichment returned error payload: %s", result)
                return None
            return result
        except Exception as exc:  # pragma: no cover - defensive guard
            logger.warning("Enrichment call failed: %s", exc)
            return None

    def _best_email_from_domain_search(self, result: Dict[str, Any]) -> Optional[str]:
        data = result.get("data") if isinstance(result, dict) else None
        emails = data.get("emails") if isinstance(data, dict) else None
        if not emails:
            return None
        sorted_emails = sorted(
            emails,
            key=lambda e: e.get("confidence", 0),
            reverse=True,
        )
        top = sorted_emails[0]
        return top.get("value") or top.get("email")

    def enrich_lead(self, lead: LeadResult) -> LeadResult:
        domain = _extract_domain(lead.business.website)
        lead.enrichment = lead.enrichment or {}

        apollo_data: Dict[str, Any] = lead.enrichment.get("apollo") or {}
        hunter_data: Dict[str, Any] = lead.enrichment.get("hunter") or {}

        # Hunter: verify known email or discover via domain search
        if self.hunter and lead.business.email:
            verified = self._safe_call(self.hunter.verify_email, lead.business.email)
            if verified:
                hunter_data.update(verified)
        elif self.hunter and domain:
            domain_result = self._safe_call(self.hunter.domain_search, domain)
            if domain_result:
                hunter_data["domain_search"] = domain_result
                best_email = self._best_email_from_domain_search(domain_result)
                if best_email and not lead.business.email:
                    lead.business.email = best_email
                    lead.business.email_source = "hunter_domain_search"
                    verified = self._safe_call(self.hunter.verify_email, best_email)
                    if verified:
                        hunter_data.update(verified)
                elif domain_result.get("rate_limited"):
                    # If rate limited, keep the error for observability but don't mutate email
                    hunter_data.update(domain_result)

        # Apollo: enrich person + organization when possible
        if self.apollo and lead.business.email:
            person = self._safe_call(self.apollo.enrich_person_by_email, lead.business.email)
            if person:
                if isinstance(person, dict):
                    if "person" in person:
                        apollo_data["person"] = person.get("person")
                    else:
                        apollo_data.update(person)
                else:
                    apollo_data["person"] = person
        if self.apollo and domain:
            org = self._safe_call(self.apollo.enrich_company_by_domain, domain)
            if org:
                if isinstance(org, dict):
                    if "organization" in org:
                        apollo_data["organization"] = org.get("organization")
                    else:
                        apollo_data.update(org)
                else:
                    apollo_data["organization"] = org

        if hunter_data:
            lead.enrichment["hunter"] = hunter_data
        if apollo_data:
            lead.enrichment["apollo"] = apollo_data

        return lead
