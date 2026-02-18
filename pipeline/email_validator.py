"""Shared email validation for the pipeline.

Single source of truth for is_invalid_email() -- used by both
extract_emails() (filter at extraction) and quality_gates.py
(filter at pack assembly).
"""

import re


# Image file patterns that should never be emails
_IMAGE_EMAIL_RE = re.compile(
    r"\.(png|jpg|jpeg|gif|svg|ico|webp|bmp)$", re.IGNORECASE
)

# Substrings that indicate non-contact emails
_INVALID_EMAIL_TOKENS = frozenset({
    "sentry", "wixpress", "cloudflare", "example.com", "test@", "noreply@",
})


def compute_email_confidence(
    hunter_result: str | None = None,
    hunter_score: int | None = None,
    apollo_confidence: int | None = None,
    source: str | None = None,
) -> int:
    """Combine multiple email verification signals into a single 0-100 confidence.

    Weights:
      - hunter_result (deliverable/risky/undeliverable): 0-40 points
      - hunter_score (0-100): scaled to 0-30 points
      - apollo_confidence (0-100): scaled to 0-20 points
      - source bonus: verified sources get +10
    """
    score = 0

    # Hunter deliverability result
    if hunter_result:
        result_lower = hunter_result.lower()
        if result_lower == "deliverable":
            score += 40
        elif result_lower == "risky":
            score += 15
        # undeliverable / unknown -> 0

    # Hunter numeric score
    if hunter_score is not None:
        score += int(hunter_score / 100 * 30)

    # Apollo confidence
    if apollo_confidence is not None:
        score += int(apollo_confidence / 100 * 20)

    # Source type bonus
    if source in ("hunter_verified", "apollo_verified", "manual_verified"):
        score += 10

    return min(score, 100)


def is_invalid_email(email) -> bool:
    """Check if an email is obviously invalid (image sprites, sentry tokens, etc.).

    Returns True if the email should be discarded. Conservative: only rejects
    patterns we have high confidence are never real contact emails.
    """
    if not email or not isinstance(email, str):
        return True
    email_lower = email.strip().lower()
    if not email_lower or "@" not in email_lower:
        return True
    if _IMAGE_EMAIL_RE.search(email_lower):
        return True
    for token in _INVALID_EMAIL_TOKENS:
        if token in email_lower:
            return True
    return False
