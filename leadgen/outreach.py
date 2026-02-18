from .ai_scoring import recommended_services
from .models import Business, WebsiteAnalysis


def _service_phrase(analysis: WebsiteAnalysis) -> str:
    services = recommended_services(analysis)
    if not services:
        return "keep your strong online presence growing"
    if len(services) == 1:
        return f"add {services[0].lower()}"
    return "add " + ", ".join(s.lower() for s in services[:-1]) + f", and {services[-1].lower()}"


def generate_outreach_message(business: Business, analysis: WebsiteAnalysis, score: int) -> str:
    """
    Deterministically returns a short outreach message tailored to detected needs.
    """
    needs_phrase = _service_phrase(analysis)
    contact_gap = []
    if not business.email:
        contact_gap.append("email capture")
    if not business.phone:
        contact_gap.append("contact options")

    contact_phrase = ""
    if contact_gap:
        if len(contact_gap) == 1:
            contact_phrase = f" and improve {contact_gap[0]}"
        else:
            contact_phrase = f" and improve {', '.join(contact_gap[:-1])} and {contact_gap[-1]}"

    return (
        f"Hi {business.name}, I noticed your site could {needs_phrase}{contact_phrase}. "
        f"We can help quickly; your lead score is {score}/100."
    )
