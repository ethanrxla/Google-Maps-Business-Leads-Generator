from leadgen.models import LeadResult, Business, WebsiteAnalysis


def test_leadresult_accepts_org_and_hunter_fields():
    lead = LeadResult(
        business=Business(name="Biz"),
        analysis=WebsiteAnalysis(
            has_website=True,
            needs_website=False,
            needs_redesign=False,
            needs_chatbot=False,
            needs_ai_integration=False,
            raw_data={},
        ),
        hunter_domain_status="found",
        hunter_suggested_emails=["a@example.com"],
        org_name="Org",
        org_website="https://org.test",
        org_linkedin_url="https://linkedin.com/company/org",
        org_industry="Tech",
        org_employee_count=50,
        org_annual_revenue=1_000_000.0,
        org_location="City, Country",
        org_is_hiring=True,
        org_job_postings_count=3,
    )
    assert lead.org_name == "Org"
    assert lead.hunter_domain_status == "found"
