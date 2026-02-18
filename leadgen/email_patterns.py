from typing import List, Optional
from urllib.parse import urlparse

from .models import Business


GENERIC_MAILBOXES = [
    "info",
    "contact",
    "hello",
    "support",
    "sales",
    "admin",
    "customerservice",
]


def _domain_from_url(website: str | None) -> Optional[str]:
    if not website:
        return None
    parsed = urlparse(website if "://" in website else f"https://{website}")
    domain = parsed.netloc or parsed.path
    if not domain or "." not in domain:
        return None
    # strip port and leading www
    domain = domain.split("@")[-1]  # in case scheme-less user@host
    domain = domain.split(":")[0]
    if domain.startswith("www."):
        domain = domain[4:]
    return domain or None


def generate_candidate_emails(
    domain: str,
    business_name: Optional[str] = None,
) -> List[str]:
    """
    Return ordered, unique role-based email candidates for a domain.
    """
    if not domain:
        return []

    candidates = [f"{box}@{domain}" for box in GENERIC_MAILBOXES]

    if business_name:
        name_lower = business_name.lower()
        if any(k in name_lower for k in ("pizza", "restaurant", "food", "eat")):
            candidates.append(f"orders@{domain}")

    seen = set()
    deduped: List[str] = []
    for email in candidates:
        if email not in seen:
            seen.add(email)
            deduped.append(email)
    return deduped


def choose_fallback_email(candidates: List[str]) -> Optional[str]:
    if candidates:
        return candidates[0]
    return None


def apply_email_patterns(business: Business) -> None:
    """
    Set business.email using pattern guessing if still missing.
    Does not overwrite existing emails.
    """
    if business.email:
        return

    domain = _domain_from_url(business.website)
    if not domain:
        return

    candidates = generate_candidate_emails(domain, business_name=business.name)
    chosen = choose_fallback_email(candidates)
    if chosen:
        business.email = chosen
        business.email_source = "pattern"
