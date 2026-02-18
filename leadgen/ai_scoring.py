from .models import LeadResult, WebsiteAnalysis


def _base_score_from_analysis(analysis: WebsiteAnalysis) -> int:
    """
    Simple heuristic scoring based on analysis flags.

    Higher scores indicate a stronger need for services.
    """
    score = 0
    if analysis.needs_website or not analysis.has_website:
        score += 70
    if analysis.needs_redesign:
        score += 20
    if analysis.needs_chatbot:
        score += 5
    if analysis.needs_ai_integration:
        score += 5
    return min(score, 100)


def score_lead(lead: LeadResult) -> int:
    """
    Returns an integer score (0–100) indicating lead quality / urgency.

    Deterministic, based solely on WebsiteAnalysis + Business fields.
    Higher = more in need of services (no website, outdated, missing chat/AI).
    """
    return _base_score_from_analysis(lead.analysis)


def recommended_services(analysis: WebsiteAnalysis) -> list[str]:
    """
    Map analysis flags to a set of recommended follow-up services.
    """
    services: list[str] = []
    if analysis.needs_website:
        services.append("Website build")
    if analysis.needs_redesign:
        services.append("Website redesign")
    if analysis.needs_chatbot:
        services.append("Chatbot")
    if analysis.needs_ai_integration:
        services.append("AI integration")
    return services


def llm_score_placeholder(lead: LeadResult) -> int:
    """
    Placeholder for future LLM-based scoring.
    Not used in tests; kept deterministic for now.
    """
    return score_lead(lead)


def lead_quality_score(lead: dict) -> int:
    """Compute an overall quality score (0-100) for a verified lead dict.

    Weights reflect the relative value of each data point for
    a sellable lead pack. Higher = more complete / more valuable.
    """
    score = 0

    if lead.get("email"):
        score += 10
    if lead.get("email_verified"):
        score += 10
    email_conf = lead.get("email_confidence") or 0
    score += int(email_conf / 100 * 10)

    if lead.get("phone"):
        score += 5
    if lead.get("phone_verified"):
        score += 5

    if lead.get("website"):
        score += 10
    if lead.get("website_alive"):
        score += 5

    if lead.get("org_name"):
        score += 5
    if lead.get("org_industry"):
        score += 5
    if lead.get("linkedin_url"):
        score += 5
    if lead.get("org_employee_count") or lead.get("org_size"):
        score += 5

    needs = lead.get("needs_score") or 0
    score += int(needs / 100 * 25)

    return min(score, 100)
