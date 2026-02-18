from leadgen.email_patterns import (
    apply_email_patterns,
    choose_fallback_email,
    generate_candidate_emails,
)
from leadgen.models import Business


def test_generate_candidate_emails_basic_order():
    candidates = generate_candidate_emails("example.com")
    assert candidates[:3] == [
        "info@example.com",
        "contact@example.com",
        "hello@example.com",
    ]
    assert len(candidates) == len(set(candidates))


def test_generate_candidate_emails_with_business_theme():
    candidates = generate_candidate_emails("coolpizza.com", business_name="Cool Pizza")
    assert "orders@coolpizza.com" in candidates


def test_choose_fallback_email():
    assert choose_fallback_email([]) is None
    assert choose_fallback_email(["info@example.com", "sales@example.com"]) == "info@example.com"


def test_apply_email_patterns_sets_email_when_missing():
    biz = Business(name="Example Biz", website="https://example.com")
    apply_email_patterns(biz)
    assert biz.email == "info@example.com"
    assert biz.email_source == "pattern"


def test_apply_email_patterns_does_not_overwrite_existing():
    biz = Business(name="Existing", website="https://example.com", email="hello@set.com", email_source="html")
    apply_email_patterns(biz)
    assert biz.email == "hello@set.com"
    assert biz.email_source == "html"
