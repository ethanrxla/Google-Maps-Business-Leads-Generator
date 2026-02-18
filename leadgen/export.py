import csv
import json
from pathlib import Path
from typing import Iterable, List

from .ai_scoring import recommended_services, score_lead
from .outreach import generate_outreach_message
from .models import LeadResult

# Keep in sync with tests/EXPECT_HEADERS
CSV_HEADERS = [
    "name",
    "address",
    "website",
    "phone",
    "email",
    "needs_website",
    "needs_redesign",
    "needs_chatbot",
    "needs_ai_integration",
    "score",
    "recommended_services",
    "outreach_message",
    "enriched_title",
    "verified_email_status",
    "apollo_company",
]

ENRICHED_EXTRA_HEADERS = [
    "tech_stack",
    "enrichment_used",
    "scrape_source",
    "email_confidence",
    "hunter_domain_status",
    "hunter_suggested_emails",
    "org_name",
    "org_website",
    "org_linkedin_url",
    "org_industry",
    "org_employee_count",
    "org_annual_revenue",
    "org_location",
    "org_is_hiring",
    "org_job_postings_count",
]


def _is_enriched_lead(lead: LeadResult) -> bool:
    return getattr(lead, "enrichment_used", None) == "enriched" or lead.tech_stack is not None


def export_csv(results: Iterable[LeadResult], output: str = "data/outputs/leads.csv") -> None:
    """
    Export a collection of LeadResult objects to a CSV file.

    Behavior (as defined by tests):
    - Always writes a header row with CSV_HEADERS (basic) or CSV_HEADERS + ENRICHED_EXTRA_HEADERS when enriched.
    - If `results` is empty, file is still created with just the header row.
    - Fields containing commas/quotes are safely CSV-escaped.
    - If the output path is invalid/unwritable, the underlying exception is propagated.
    """
    output_path = Path(output)
    leads: List[LeadResult] = list(results)
    enriched_mode = any(_is_enriched_lead(l) for l in leads)
    headers = CSV_HEADERS + ENRICHED_EXTRA_HEADERS if enriched_mode else CSV_HEADERS

    with output_path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=headers)
        writer.writeheader()

        for lead in leads:
            score = score_lead(lead)
            services = recommended_services(lead.analysis)
            row = {
                "name": lead.business.name,
                "address": lead.business.address,
                "website": lead.business.website,
                "phone": lead.business.phone,
                "email": lead.business.email,
                "needs_website": lead.analysis.needs_website,
                "needs_redesign": lead.analysis.needs_redesign,
                "needs_chatbot": lead.analysis.needs_chatbot,
                "needs_ai_integration": lead.analysis.needs_ai_integration,
                "score": score,
                "recommended_services": ", ".join(services),
                "outreach_message": generate_outreach_message(
                    lead.business, lead.analysis, score
                ),
                "enriched_title": (lead.enrichment or {}).get("apollo", {}).get("person", {}).get("title", "") if lead.enrichment else "",
                "verified_email_status": (lead.enrichment or {}).get("hunter", {}).get("result") if lead.enrichment else "",
                "apollo_company": (lead.enrichment or {}).get("apollo", {}).get("person", {}).get("organization", ""),
            }
            if enriched_mode:
                row.update(
                    {
                        "tech_stack": json.dumps(lead.tech_stack) if lead.tech_stack is not None else "",
                        "enrichment_used": lead.enrichment_used or "",
                        "scrape_source": lead.scrape_source or "",
                        "email_confidence": lead.email_confidence or "",
                        "hunter_domain_status": lead.hunter_domain_status or "",
                        "hunter_suggested_emails": ", ".join(lead.hunter_suggested_emails) if lead.hunter_suggested_emails else "",
                        "org_name": lead.org_name or "",
                        "org_website": lead.org_website or "",
                        "org_linkedin_url": lead.org_linkedin_url or "",
                        "org_industry": lead.org_industry or "",
                        "org_employee_count": lead.org_employee_count if lead.org_employee_count is not None else "",
                        "org_annual_revenue": lead.org_annual_revenue if lead.org_annual_revenue is not None else "",
                        "org_location": lead.org_location or "",
                        "org_is_hiring": lead.org_is_hiring if lead.org_is_hiring is not None else "",
                        "org_job_postings_count": lead.org_job_postings_count if lead.org_job_postings_count is not None else "",
                    }
                )
            writer.writerow(row)


def export_jsonl(leads: list[LeadResult], output: str) -> None:
    output_path = Path(output)
    with output_path.open("w", encoding="utf-8") as f:
        for lead in leads:
            services = recommended_services(lead.analysis)
            score = score_lead(lead)
            outreach_message = generate_outreach_message(
                lead.business, lead.analysis, score
            )
            obj = {
                "name": lead.business.name,
                "address": lead.business.address,
                "phone": lead.business.phone,
                "email": lead.business.email,
                "website": lead.business.website,
                "score": score,
                "recommended_services": services,
                "outreach_message": outreach_message,
            }
            if lead.business.email_source:
                obj["email_source"] = lead.business.email_source
            if _is_enriched_lead(lead):
                obj["tech_stack"] = lead.tech_stack
                obj["scrape_source"] = lead.scrape_source or "basic_html"
                obj["enrichment_used"] = lead.enrichment_used or "enriched"
                if lead.email_confidence is not None:
                    obj["email_confidence"] = lead.email_confidence
                if lead.hunter_domain_status is not None:
                    obj["hunter_domain_status"] = lead.hunter_domain_status
                if lead.hunter_suggested_emails:
                    obj["hunter_suggested_emails"] = lead.hunter_suggested_emails
                if lead.org_name:
                    obj["org_name"] = lead.org_name
                if lead.org_website:
                    obj["org_website"] = lead.org_website
                if lead.org_linkedin_url:
                    obj["org_linkedin_url"] = lead.org_linkedin_url
                if lead.org_industry:
                    obj["org_industry"] = lead.org_industry
                if lead.org_employee_count is not None:
                    obj["org_employee_count"] = lead.org_employee_count
                if lead.org_annual_revenue is not None:
                    obj["org_annual_revenue"] = lead.org_annual_revenue
                if lead.org_location:
                    obj["org_location"] = lead.org_location
                if lead.org_is_hiring is not None:
                    obj["org_is_hiring"] = lead.org_is_hiring
                if lead.org_job_postings_count is not None:
                    obj["org_job_postings_count"] = lead.org_job_postings_count
            if lead.enrichment:
                obj["enrichment"] = lead.enrichment
            f.write(json.dumps(obj) + "\n")
