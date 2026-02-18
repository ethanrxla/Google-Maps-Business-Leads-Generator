import pytest

from leadgen.ai_scoring import lead_quality_score, recommended_services, score_lead
from leadgen.models import Business, LeadResult, WebsiteAnalysis


def _lead_with_analysis(**analysis_flags) -> LeadResult:
    analysis = WebsiteAnalysis(
        raw_data={},
        **analysis_flags,
    )
    business = Business(
        name="Test Biz",
        address=None,
        website="https://example.com" if analysis.has_website else None,
        phone=None,
        place_id="pid",
    )
    return LeadResult(business=business, analysis=analysis)


def test_score_lead_orders_by_need():
    no_site = _lead_with_analysis(
        has_website=False,
        needs_website=True,
        needs_redesign=True,
        needs_chatbot=True,
        needs_ai_integration=True,
    )
    outdated = _lead_with_analysis(
        has_website=True,
        needs_website=False,
        needs_redesign=True,
        needs_chatbot=True,
        needs_ai_integration=True,
    )
    decent = _lead_with_analysis(
        has_website=True,
        needs_website=False,
        needs_redesign=False,
        needs_chatbot=True,
        needs_ai_integration=True,
    )
    perfect = _lead_with_analysis(
        has_website=True,
        needs_website=False,
        needs_redesign=False,
        needs_chatbot=False,
        needs_ai_integration=False,
    )

    score_no_site = score_lead(no_site)
    score_outdated = score_lead(outdated)
    score_decent = score_lead(decent)
    score_perfect = score_lead(perfect)

    assert score_no_site > score_outdated > score_decent > score_perfect
    assert all(0 <= s <= 100 for s in [score_no_site, score_outdated, score_decent, score_perfect])


@pytest.mark.parametrize(
    "flags,expected",
    [
        (
            dict(
                has_website=False,
                needs_website=True,
                needs_redesign=True,
                needs_chatbot=True,
                needs_ai_integration=True,
            ),
            ["Website build", "Website redesign", "Chatbot", "AI integration"],
        ),
        (
            dict(
                has_website=True,
                needs_website=False,
                needs_redesign=False,
                needs_chatbot=True,
                needs_ai_integration=False,
            ),
            ["Chatbot"],
        ),
        (
            dict(
                has_website=True,
                needs_website=False,
                needs_redesign=False,
                needs_chatbot=False,
                needs_ai_integration=False,
            ),
            [],
        ),
    ],
)
def test_recommended_services_mapping(flags, expected):
    analysis = WebsiteAnalysis(raw_data={}, **flags)
    assert recommended_services(analysis) == expected


# ---------------------------------------------------------------------------
# lead_quality_score (dict-based scoring for verified leads)
# ---------------------------------------------------------------------------

class TestLeadQualityScore:
    def test_empty_lead(self):
        assert lead_quality_score({}) == 0

    def test_maximum_score_capped_at_100(self):
        lead = {
            "email": "a@b.com",
            "email_verified": True,
            "email_confidence": 100,
            "phone": "555-1234",
            "phone_verified": True,
            "website": "https://example.com",
            "website_alive": True,
            "org_name": "Acme",
            "org_industry": "Tech",
            "linkedin_url": "https://linkedin.com/in/x",
            "org_employee_count": 50,
            "needs_score": 100,
        }
        assert lead_quality_score(lead) == 100

    def test_email_fields(self):
        assert lead_quality_score({"email": "a@b.com"}) == 10
        assert lead_quality_score({"email": "a@b.com", "email_verified": True}) == 20
        assert lead_quality_score({"email_confidence": 50}) == 5

    def test_phone_fields(self):
        assert lead_quality_score({"phone": "555"}) == 5
        assert lead_quality_score({"phone": "555", "phone_verified": True}) == 10

    def test_website_fields(self):
        assert lead_quality_score({"website": "https://x.com"}) == 10
        assert lead_quality_score({"website": "https://x.com", "website_alive": True}) == 15

    def test_org_fields(self):
        assert lead_quality_score({"org_name": "Acme"}) == 5
        assert lead_quality_score({"org_industry": "Tech"}) == 5
        assert lead_quality_score({"linkedin_url": "https://li.com"}) == 5
        assert lead_quality_score({"org_employee_count": 10}) == 5

    def test_needs_score_scaling(self):
        assert lead_quality_score({"needs_score": 100}) == 25
        assert lead_quality_score({"needs_score": 50}) == 12
        assert lead_quality_score({"needs_score": 0}) == 0

    def test_ordering(self):
        """More complete leads should score higher."""
        minimal = lead_quality_score({"email": "a@b.com"})
        medium = lead_quality_score({
            "email": "a@b.com", "phone": "555",
            "website": "https://x.com",
        })
        full = lead_quality_score({
            "email": "a@b.com", "email_verified": True,
            "phone": "555", "website": "https://x.com",
            "org_name": "Acme", "needs_score": 80,
        })
        assert full > medium > minimal
