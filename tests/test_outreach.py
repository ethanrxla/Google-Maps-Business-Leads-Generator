from leadgen.outreach import generate_outreach_message
from leadgen.models import Business, WebsiteAnalysis


def _analysis(needs_website=False, needs_redesign=False, needs_chatbot=False, needs_ai=False):
    return WebsiteAnalysis(
        has_website=not needs_website,
        needs_website=needs_website,
        needs_redesign=needs_redesign,
        needs_chatbot=needs_chatbot,
        needs_ai_integration=needs_ai,
        raw_data={},
    )


def test_outreach_mentions_detected_services():
    business = Business(name="Cafe Delight", email=None, phone=None)
    analysis = _analysis(needs_redesign=True, needs_chatbot=True, needs_ai=True)
    message = generate_outreach_message(business, analysis, score=80)

    assert "website redesign" in message.lower()
    assert "chatbot" in message.lower()
    assert "ai" in message.lower()
    assert "email capture" in message.lower()
    assert "contact options" in message.lower()


def test_outreach_when_no_needs_keeps_positive():
    business = Business(name="Modern Co", email="info@modern.co", phone="555-0000")
    analysis = _analysis()
    message = generate_outreach_message(business, analysis, score=20)

    assert "strong online presence" in message.lower()
    assert "20/100" in message


def test_outreach_varies_with_website_need():
    business = Business(name="New Biz", email=None, phone="555-2222")
    analysis = _analysis(needs_website=True, needs_redesign=True, needs_chatbot=False, needs_ai=False)
    message = generate_outreach_message(business, analysis, score=90)

    assert "website build" in message.lower()
    assert "redesign" in message.lower()
