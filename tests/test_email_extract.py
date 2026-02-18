from leadgen.email_extract import extract_emails
from leadgen.models import Business


def test_extract_emails_none_or_empty_returns_empty():
    assert extract_emails(None) == []
    assert extract_emails("") == []


def test_extracts_plain_email_in_text():
    html = "<p>Contact us at hello@dentistmiami.com for info.</p>"
    assert extract_emails(html) == ["hello@dentistmiami.com"]


def test_extracts_mailto_link():
    html = '<a href="mailto:sales@mybiz.com">Email us</a>'
    assert extract_emails(html) == ["sales@mybiz.com"]


def test_multiple_emails_preserve_order_and_uniqueness():
    html = """
    <p>Primary: contact@dentistmiami.com</p>
    <a href="mailto:contact@dentistmiami.com">duplicate</a>
    <p>Secondary: support@dentistboca.org</p>
    """
    emails = extract_emails(html)
    assert emails == ["contact@dentistmiami.com", "support@dentistboca.org"]

    biz = Business(name="Test")
    if biz.email is None and emails:
        biz.email = emails[0]
    assert biz.email == "contact@dentistmiami.com"


# ---------------------------------------------------------------------------
# Day 2: Filtering integration tests
# ---------------------------------------------------------------------------

class TestExtractEmailsFiltering:
    """extract_emails() must filter out known-invalid patterns before returning."""

    def test_image_sprite_emails_excluded(self):
        html = """
        <p>Email: info@dentist.com</p>
        <img src="fancybox_sprite@2x.png" />
        <img src="logo@brand.jpg" />
        """
        emails = extract_emails(html)
        assert emails == ["info@dentist.com"]

    def test_sentry_dsn_excluded(self):
        html = """
        <p>Contact: hello@mybiz.com</p>
        <script>Sentry.init({dsn: "https://abc123@o456.ingest.sentry.io/789"})</script>
        """
        emails = extract_emails(html)
        assert emails == ["hello@mybiz.com"]

    def test_wixpress_excluded(self):
        html = """
        <p>info@realdentist.com</p>
        <meta content="something@wixpress.com" />
        """
        emails = extract_emails(html)
        assert emails == ["info@realdentist.com"]

    def test_noreply_excluded(self):
        html = """
        <p>team@realcompany.com</p>
        <p>noreply@realcompany.com</p>
        """
        emails = extract_emails(html)
        assert emails == ["team@realcompany.com"]

    def test_all_invalid_returns_empty(self):
        html = """
        <img src="fancybox_sprite@2x.png" />
        <script>dsn: "abc@o1.ingest.sentry.io"</script>
        """
        assert extract_emails(html) == []

    def test_cloudflare_email_excluded(self):
        html = """
        <p>real@dentist.com</p>
        <p>protection@cloudflare.com</p>
        """
        emails = extract_emails(html)
        assert emails == ["real@dentist.com"]

    def test_example_com_excluded(self):
        html = """
        <p>real@dentist.com</p>
        <p>test@example.com</p>
        """
        emails = extract_emails(html)
        assert emails == ["real@dentist.com"]
