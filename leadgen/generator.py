import json
import logging
from pathlib import Path
from typing import Dict, List, Optional
from urllib.parse import urljoin

from leadgen.analysis import analyze_html
from leadgen.email_extract import extract_emails
from leadgen.email_patterns import apply_email_patterns
from leadgen.export import export_csv, export_jsonl
from leadgen.ai_scoring import score_lead
from leadgen.enrichment import LeadEnricher, _extract_domain, is_enrichment_error as _is_enrichment_error
from leadgen.integrations import builtwith_client, scrapingbee_client
from leadgen.integrations.hunter_client import hunter_domain_search
from leadgen.integrations.apollo_client import apollo_bulk_org_enrich, apollo_get_org_job_postings
from leadgen.models import LeadResult
from leadgen.outreach import generate_outreach_message
from leadgen.paths import build_pack_paths, slugify
from leadgen.places import get_details, search_places
from leadgen.website_fetch import fetch_html
from pipeline.quality_gates import check_quality_gates

logger = logging.getLogger(__name__)


def make_pack_id(
    country: Optional[str],
    state: Optional[str],
    county: Optional[str],
    city: Optional[str],
    niche: Optional[str],
    limit: int,
) -> str:
    """
    Build a stable, slugified pack_id from location + niche + limit.
    """
    parts: List[str] = []
    for component in (country, state, county, city, niche):
        if component:
            slug = slugify(component)
            if slug:
                parts.append(slug)
    parts.append(str(limit))
    return "_".join(parts)


def generate_pack(
    query: str,
    country: Optional[str],
    state: Optional[str],
    county: Optional[str],
    city: Optional[str],
    niche: Optional[str],
    limit: int,
    pack_id: str,
    base_dir: Path = Path("data/packs"),
    output_csv: Optional[Path] = None,
    output_jsonl: Optional[Path] = None,
    businesses=None,
    status: Optional[str] = None,
    enrichment_tier: str = "basic",
) -> Dict:
    """
    Run the full pipeline to generate a lead pack and write CSV/JSONL files.

    Intended for both CLI and backend-driven pack generation. Returns summary:
    {
        "pack_id": pack_id,
        "csv_path": Path,
        "jsonl_path": Path | None,
        "lead_count": int,
        "status": status,
    }
    """
    # Determine output paths
    if output_csv is None:
        basename = pack_id or (slugify(query) if query else "leads")
        csv_path, jsonl_path_default = build_pack_paths(
            base_dir=base_dir,
            country=country,
            state=state,
            county=county,
            city=city,
            niche=niche,
            default_basename=basename,
        )
        output_csv = csv_path
        if output_jsonl is None:
            output_jsonl = jsonl_path_default

    output_csv = Path(output_csv)
    output_csv.parent.mkdir(parents=True, exist_ok=True)
    if output_jsonl:
        output_jsonl = Path(output_jsonl)
        output_jsonl.parent.mkdir(parents=True, exist_ok=True)

    # Search if not provided
    if businesses is None:
        businesses, status = search_places(query, limit=limit, include_status=True)
    else:
        # If status wasn't passed, keep whatever came in
        status = status

    results: List[LeadResult] = []
    scrapingbee = None
    builtwith = None
    if enrichment_tier == "enriched":
        try:
            scrapingbee = scrapingbee_client.ScrapingBeeClient()  # type: ignore
        except Exception:
            scrapingbee = None
        try:
            builtwith = builtwith_client.BuiltWithClient()  # type: ignore
        except Exception:
            builtwith = None
    for business in businesses:
        business = get_details(business)
        html = fetch_html(business.website) if business.website else None
        scrape_source = None
        if enrichment_tier == "enriched" and business.website:
            if not html or _looks_js_blocked(html):
                if scrapingbee:
                    try:
                        fallback_html = scrapingbee.fetch(business.website)
                    except Exception:
                        fallback_html = None
                    if fallback_html:
                        html = fallback_html
                        scrape_source = "scrapingbee_fallback"
            if scrape_source is None:
                scrape_source = "basic_html"
        emails = extract_emails(html)
        if business.email is None and emails:
            business.email = emails[0]
            business.email_source = "html"

        if business.email is None and business.website:
            contact_html = _fetch_contact_page_html(
                business.website,
                fetch_html,
                scrapingbee if enrichment_tier == "enriched" else None,
            )
            if contact_html:
                contact_emails = extract_emails(contact_html)
                if business.email is None and contact_emails:
                    business.email = contact_emails[0]
                    business.email_source = "contact_page"
                    emails = contact_emails
                if not html:
                    html = contact_html
        apply_email_patterns(business)
        analysis = analyze_html(html)
        # Outreach is derived at export time; we just package LeadResult.
        results.append(
            LeadResult(
                business=business,
                analysis=analysis,
                scrape_source=scrape_source if enrichment_tier == "enriched" else None,
                enrichment_used="enriched" if enrichment_tier == "enriched" else "basic",
            )
        )

    if enrichment_tier == "enriched":
        apollo = None
        hunter = None
        try:
            from leadgen.integrations.apollo_client import ApolloClient  # type: ignore
            apollo = ApolloClient()
        except Exception:
            apollo = None
        try:
            from leadgen.integrations.hunter_client import HunterClient  # type: ignore
            hunter = HunterClient()
        except Exception:
            hunter = None

        enricher = LeadEnricher(apollo_client=apollo, hunter_client=hunter)
        # Prepare caches for org-level enrichment
        logger.info("enrichment.start", extra={"tier": enrichment_tier, "num_leads": len(results)})
        domains = []
        for lead in results:
            domain = _extract_domain(lead.business.website)
            if domain:
                domains.append(domain.lower())
        apollo_org_cache = apollo_bulk_org_enrich(list({d for d in domains})) if apollo else {}
        if apollo_org_cache:
            logger.info("enrichment.apollo.bulk_org", extra={"domains_count": len(apollo_org_cache)})
        hunter_domain_cache = {}
        job_postings_cache = {}

        for lead in results:
            try:
                domain = _extract_domain(lead.business.website)
                domain_key = domain.lower() if domain else None
                if domain_key:
                    if domain_key not in hunter_domain_cache:
                        hunter_domain_cache[domain_key] = hunter_domain_search(domain_key, client=hunter)
                    hunter_data = hunter_domain_cache.get(domain_key)
                    if hunter_data:
                        lead.hunter_domain_status = "found"
                        data = hunter_data.get("data") if isinstance(hunter_data, dict) else {}
                        emails = data.get("emails") or []
                        suggested = []
                        for item in emails:
                            val = item.get("value") or item.get("email")
                            if val:
                                suggested.append(val)
                                if lead.email_confidence is None and item.get("confidence") is not None:
                                    lead.email_confidence = str(item.get("confidence"))
                        if suggested:
                            lead.hunter_suggested_emails = suggested
                            if lead.business.email is None:
                                lead.business.email = suggested[0]
                                lead.business.email_source = "hunter_domain_search"
                    elif hunter is not None:
                        lead.hunter_domain_status = "not_found"

                org_data = apollo_org_cache.get(domain_key) if domain_key else None
                if org_data:
                    lead.org_name = org_data.get("name")
                    lead.org_website = org_data.get("website_url") or org_data.get("domain")
                    lead.org_linkedin_url = org_data.get("linkedin_url")
                    lead.org_industry = org_data.get("industry") or (org_data.get("industries") or [None])[0]
                    lead.org_employee_count = org_data.get("employee_count")
                    lead.org_annual_revenue = org_data.get("estimated_annual_revenue")
                    hq = org_data.get("headquarters_location") or {}
                    if isinstance(hq, dict):
                        city = hq.get("city")
                        state = hq.get("state") or hq.get("province")
                        country = hq.get("country")
                        lead.org_location = ", ".join([p for p in [city, state, country] if p])
                    org_id = org_data.get("id") or org_data.get("organization_id")
                    if org_id:
                        if org_id not in job_postings_cache:
                            job_postings_cache[org_id] = apollo_get_org_job_postings(org_id, client=apollo)  # type: ignore
                        job = job_postings_cache.get(org_id)
                        if job:
                            lead.org_is_hiring = job.get("is_hiring")
                            lead.org_job_postings_count = job.get("count")

                if builtwith and lead.business.website:
                    domain = lead.business.website
                    tech_stack = builtwith.tech_lookup(domain)
                    if tech_stack and not _is_enrichment_error(tech_stack):
                        lead.tech_stack = tech_stack
                        lead.enrichment = lead.enrichment or {}
                        lead.enrichment["tech_stack"] = tech_stack
                enricher.enrich_lead(lead)
                # Best-effort email confidence from enrichment data
                hunter_data = (lead.enrichment or {}).get("hunter", {}) if lead.enrichment else {}
                apollo_data = (lead.enrichment or {}).get("apollo", {}) if lead.enrichment else {}
                confidence = hunter_data.get("score") or hunter_data.get("result") or apollo_data.get("confidence")
                if confidence is not None:
                    lead.email_confidence = str(confidence)
            except Exception:
                # Soft-fail enrichment
                continue

    quality_rows = [_to_quality_gate_row(lead) for lead in results]
    sellable, raw_quality_gate_failures = check_quality_gates(
        quality_rows,
        target_count=limit,
        enriched=(enrichment_tier == "enriched"),
    )
    # Keep artifact output deterministic across runs and always expose explicit
    # reasons when a pack is unsellable.
    quality_gate_failures = sorted(str(reason) for reason in (raw_quality_gate_failures or []))

    # Fail-closed enforcement for sellable packs:
    # any explicit gate failure reason must force sellable=false,
    # even if an upstream gate implementation accidentally reports sellable=true.
    if quality_gate_failures:
        sellable = False

    if not sellable and not quality_gate_failures:
        quality_gate_failures = ["quality_gate_failed_without_explicit_reason"]

    export_csv(results, str(output_csv))
    if output_jsonl:
        export_jsonl(results, str(output_jsonl))

    summary = {
        "pack_id": pack_id,
        "csv_path": output_csv,
        "jsonl_path": output_jsonl,
        "lead_count": len(results),
        "status": status,
        "sellable": sellable,
        "quality_gate_failures": quality_gate_failures,
    }
    summary_path = _write_pack_summary_artifact(output_csv, summary)
    summary["summary_path"] = summary_path
    return summary


def _looks_js_blocked(html: Optional[str]) -> bool:
    if not html:
        return True
    text = html.strip().lower()
    if not text:
        return True
    return "enable javascript" in text or "please enable js" in text


def _fetch_contact_page_html(
    website: str,
    fetcher,
    scrapingbee_client,
) -> Optional[str]:
    paths = ("contact", "contact-us", "about")
    for path in paths:
        contact_url = urljoin(website.rstrip("/") + "/", path)
        try:
            html = fetcher(contact_url)
        except Exception:
            html = None
        if html and html.strip():
            return html
        if scrapingbee_client and (not html or _looks_js_blocked(html)):
            try:
                fallback_html = scrapingbee_client.fetch(contact_url)
            except Exception:
                fallback_html = None
            if fallback_html and fallback_html.strip():
                return fallback_html
    return None


def _to_quality_gate_row(lead: LeadResult) -> dict:
    name_normalized = slugify(lead.business.name or "") if lead.business.name else ""
    dedup_key = name_normalized or (lead.business.website or lead.business.email or "")
    verified_status = (lead.enrichment or {}).get("hunter", {}).get("result") if lead.enrichment else None
    email_verified = verified_status == "deliverable"
    return {
        "email": lead.business.email,
        "email_verified": email_verified,
        "phone": lead.business.phone,
        "website": lead.business.website,
        "dedup_key": dedup_key,
        "name_normalized": name_normalized,
        "data_freshness_days": 0,
        "needs_score": score_lead(lead),
    }


def _write_pack_summary_artifact(output_csv: Path, summary: Dict) -> Path:
    summary_path = output_csv.with_suffix(".summary.json")
    artifact = {
        "pack_id": summary["pack_id"],
        "lead_count": summary["lead_count"],
        "status": summary["status"],
        "sellable": summary["sellable"],
        "quality_gate_failures": summary["quality_gate_failures"],
    }
    summary_path.write_text(json.dumps(artifact, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return summary_path
