import pytest
from leadgen.analysis import analyze_html
from leadgen.models import WebsiteAnalysis


def test_analyze_html_none_needs_website():
    """If HTML is None, we treat it as no website and needing everything."""
    result = analyze_html(None)
    assert isinstance(result, WebsiteAnalysis)
    assert result.has_website is False
    assert result.needs_website is True
    assert result.needs_redesign is True
    assert result.needs_chatbot is True
    assert result.needs_ai_integration is True


def test_analyze_html_empty_string_needs_website():
    """Empty string should behave similar to missing website."""
    result = analyze_html("")
    assert result.has_website is False
    assert result.needs_website is True


def test_analyze_html_responsive_site_not_needing_redesign():
    html = """
    <html>
      <head>
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Modern Site</title>
      </head>
      <body>
        <p>&copy; 2024 Modern Business</p>
      </body>
    </html>
    """
    result = analyze_html(html)
    assert result.has_website is True
    assert result.needs_website is False
    # Responsive + recent year should count as "not needing redesign"
    assert result.needs_redesign is False
    assert result.raw_data.get("responsive") is True
    assert result.raw_data.get("recent") is True


def test_analyze_html_outdated_site_needs_redesign():
    html = """
    <html>
      <head>
        <title>Old Site</title>
      </head>
      <body>
        <p>Welcome to our website.</p>
        <p>&copy; 2010 Old Corp</p>
      </body>
    </html>
    """
    result = analyze_html(html)
    assert result.has_website is True
    assert result.needs_website is False
    # No viewport, no modern CSS, no recent year => redesign recommended
    assert result.needs_redesign is True


def test_analyze_html_detects_bootstrap_as_modern():
    html = """
    <html>
      <head>
        <link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css">
      </head>
      <body>
        <p>Bootstrap based site.</p>
      </body>
    </html>
    """
    result = analyze_html(html)
    assert result.has_website is True
    assert result.needs_website is False
    # Bootstrap should mark it as modern enough not to need redesign
    assert result.needs_redesign is False
    assert result.raw_data.get("modern_css") is True


def test_analyze_html_detects_chat_widget():
    html = """
    <html>
      <body>
        <script src="https://embed.tawk.to/some-chat-widget.js"></script>
      </body>
    </html>
    """
    result = analyze_html(html)
    assert result.has_website is True
    assert result.needs_chatbot is False  # already has one


def test_analyze_html_no_chat_widget_needs_chatbot():
    html = """
    <html>
      <body>
        <h1>Contact Us</h1>
        <p>Call us for more info.</p>
      </body>
    </html>
    """
    result = analyze_html(html)
    assert result.has_website is True
    assert result.needs_chatbot is True


def test_analyze_html_detects_ai_keywords():
    html = """
    <html>
      <body>
        <p>Our AI assistant is powered by ChatGPT and OpenAI.</p>
      </body>
    </html>
    """
    result = analyze_html(html)
    assert result.has_website is True
    assert result.needs_ai_integration is False  # already has AI mentioned
