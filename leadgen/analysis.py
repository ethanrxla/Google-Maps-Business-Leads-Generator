from bs4 import BeautifulSoup
from .models import WebsiteAnalysis

CHAT_WIDGET_KEYWORDS = [
    "tawk.to", "intercom", "drift", "livechat",
    "tidio", "crisp.chat", "chatbot"
]

AI_KEYWORDS = [
    "ai assistant", "chatgpt", "openai", "powered by ai",
]

def analyze_html(html: str | None):
    if not html:
        return WebsiteAnalysis(
            has_website=False,
            needs_website=True,
            needs_redesign=True,
            needs_chatbot=True,
            needs_ai_integration=True,
            raw_data={}
        )

    soup = BeautifulSoup(html, "html.parser")
    text = soup.get_text(" ", strip=True).lower()
    html_lower = html.lower()

    # Heuristics
    is_responsive = bool(soup.find("meta", attrs={"name": "viewport"}))
    modern_css = "bootstrap" in html_lower or "tailwind" in html_lower
    recent = any(str(y) in text for y in range(2022, 2026))

    has_chat = any(k in html_lower for k in CHAT_WIDGET_KEYWORDS)
    has_ai = any(k in text for k in AI_KEYWORDS)

    needs_redesign = not (is_responsive or modern_css or recent)

    return WebsiteAnalysis(
        has_website=True,
        needs_website=False,
        needs_redesign=needs_redesign,
        needs_chatbot=not has_chat,
        needs_ai_integration=not has_ai,
        raw_data={
            "responsive": is_responsive,
            "modern_css": modern_css,
            "recent": recent
        }
    )
