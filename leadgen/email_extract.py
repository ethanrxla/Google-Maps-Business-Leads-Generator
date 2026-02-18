import re
from typing import List

from pipeline.email_validator import is_invalid_email

EMAIL_PATTERN = re.compile(
    r"(?i)(?:mailto:)?([a-z0-9._%+-]+@[a-z0-9.-]+\.[a-z]{2,})"
)


def extract_emails(html: str | None) -> List[str]:
    """
    Deterministically extracts email-like strings from HTML using regex.
    Captures plain emails and mailto links; returns ordered unique list.
    Filters out known-invalid patterns (image sprites, sentry DSNs, etc.).
    """
    if not html:
        return []

    matches = EMAIL_PATTERN.findall(html)
    # Preserve order while deduping, filter invalid
    seen = set()
    emails = []
    for email in matches:
        lower = email.lower()
        if lower not in seen and not is_invalid_email(email):
            seen.add(lower)
            emails.append(email)
    return emails
