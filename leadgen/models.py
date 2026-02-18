from dataclasses import dataclass
from typing import Dict, Optional, List


@dataclass
class Business:
    name: str
    address: Optional[str] = None
    website: Optional[str] = None
    phone: Optional[str] = None
    email: Optional[str] = None
    email_source: Optional[str] = None
    place_id: Optional[str] = None


@dataclass
class WebsiteAnalysis:
    has_website: bool
    needs_website: bool
    needs_redesign: bool
    needs_chatbot: bool
    needs_ai_integration: bool
    raw_data: Dict = None


@dataclass
class LeadResult:
    business: Business
    analysis: WebsiteAnalysis
    enrichment: Optional[Dict] = None
    tech_stack: Optional[Dict] = None
    scrape_source: Optional[str] = None
    enrichment_used: Optional[str] = None
    email_confidence: Optional[str] = None
    # Hunter domain/email enrichment
    hunter_domain_status: Optional[str] = None
    hunter_suggested_emails: Optional[List[str]] = None
    # Apollo org enrichment
    org_name: Optional[str] = None
    org_website: Optional[str] = None
    org_linkedin_url: Optional[str] = None
    org_industry: Optional[str] = None
    org_employee_count: Optional[int] = None
    org_annual_revenue: Optional[float] = None
    org_location: Optional[str] = None
    # Apollo job postings
    org_is_hiring: Optional[bool] = None
    org_job_postings_count: Optional[int] = None
