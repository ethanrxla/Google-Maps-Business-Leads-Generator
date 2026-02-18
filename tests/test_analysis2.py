import pytest
from leadgen.analysis import analyze_html
from leadgen.models import WebsiteAnalysis


def test_analyze_html_none_needs_website():
    """If HTML is None, treat it as no website and needing everything."""
    result = analyze_html(None)

    assert isinstance(result, WebsiteAnalysis)
    assert result.has_website is False
    assert result.needs_website is True
    assert result.needs_redesign is True
    assert result.needs_chatbot is True
    assert result.needs_ai_integration is True
    # raw_data should at least be a dict
    assert isinstance(result.raw_data, dict)


def test_analyze_html_empty_string_needs_website():
    """Empty string should behave similar to missing website."""
    result = analyze_html("")

    assert isinstance(result, WebsiteAnalysis)
    assert result.has_website is False
    assert result.needs_website is True


def test_analyze_html_responsive_site_not_needing_redesign():
    """Viewport meta + recent year should count as a modern site."""
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
    assert result.needs_redesign is False
    assert result.raw_data.get("responsive") is True
    assert result.raw_data.get("recent") is True


def test_analyze_html_outdated_site_needs_redesign():
    """No viewport, no modern CSS, no recent year => redesign recommended."""
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
    assert result.needs_redesign is True
    assert result.raw_data.get("responsive") is False
    assert result.raw_data.get("modern_css") is False
    assert result.raw_data.get("recent") is False


def test_analyze_html_detects_bootstrap_as_modern():
    """Bootstrap CSS link should mark the site as modern enough."""
    html = """
    <html>
      <head>
        <link rel="stylesheet"
              href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css">
      </head>
      <body>
        <p>Bootstrap based site.</p>
      </body>
    </html>
    """
    result = analyze_html(html)

    assert result.has_website is True
    assert result.needs_website is False
    assert result.needs_redesign is False
    assert result.raw_data.get("modern_css") is True


def test_analyze_html_detects_chat_widget():
    """Presence of a known chat widget script should mean no chatbot needed."""
    html = """
    <html>
      <body>
        <script src="https://widget.tawk.to/123/abc"></script>
      </body>
    </html>
    """
    result = analyze_html(html)

    assert result.has_website is True
    assert result.needs_chatbot is False  # already has one


def test_analyze_html_no_chat_widget_needs_chatbot():
    """No known chat widget => site is a candidate for chatbot."""
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


def test_analyze_html_detects_recent_dates():
    """Recent years mentioned in text should set the 'recent' flag."""
    html = "<html><body>Copyright 2024</body></html>"

    result = analyze_html(html)

    assert result.has_website is True
    assert result.needs_website is False
    assert result.raw_data.get("recent") is True
    # With recency, we generally should not need a redesign
    assert result.needs_redesign is False


def test_analyze_html_detects_ai_keywords():
    """AI-related keywords should mean AI integration is already present."""
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


def test_analyze_html_perfect_site_does_not_need_anything():
    """
    A 'perfect' site with modern features, chatbot, and AI
    should not be flagged as needing redesign, chatbot, or AI.
    """
    html = """
    <html>
      <head>
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <link rel="stylesheet"
              href="https://stackpath.bootstrapcdn.com/bootstrap/4.3.1/css/bootstrap.min.css">
      </head>
      <body>
        <p>Copyright 2024. All rights reserved.</p>
        <script src="https://widget.tawk.to/123/abc"></script>
        <p>Our new AI assistant is here to help!</p>
      </body>
    </html>
    """
    result = analyze_html(html)

    assert result.has_website is True
    assert result.needs_website is False
    assert result.needs_redesign is False
    assert result.needs_chatbot is False
    assert result.needs_ai_integration is False
    assert result.raw_data.get("responsive") is True
    assert result.raw_data.get("modern_css") is True
    assert result.raw_data.get("recent") is True
