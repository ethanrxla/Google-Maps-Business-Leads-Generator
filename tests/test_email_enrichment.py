from leadgen.email_patterns import apply_email_patterns
from leadgen.models import Business


def test_pattern_guessing_runs_when_no_email_sources():
    biz = Business(name="Pattern Test", website="pattern.com")
    assert biz.email is None

    apply_email_patterns(biz)

    assert biz.email == "info@pattern.com"
    assert biz.email_source == "pattern"


def test_pattern_guessing_skipped_without_domain():
    biz = Business(name="No Domain")
    apply_email_patterns(biz)
    assert biz.email is None


def test_pattern_guessing_does_not_overwrite():
    biz = Business(name="Has Email", website="example.com", email="from@html.com", email_source="html")
    apply_email_patterns(biz)
    assert biz.email == "from@html.com"
    assert biz.email_source == "html"
