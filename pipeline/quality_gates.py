"""Quality gate enforcement for lead packs.

A pack must pass ALL gates to be marked sellable=true.
Each gate returns a failure reason string or None if passed.
The top-level check_quality_gates() returns (pass: bool, failures: list[str]).
"""

from typing import Optional

from pipeline.email_validator import is_invalid_email  # noqa: F401 -- re-exported


# ---------------------------------------------------------------------------
# Individual gates
# ---------------------------------------------------------------------------

def _gate_email_coverage(leads: list[dict], enriched: bool) -> Optional[str]:
    """Check % of leads with a non-empty email."""
    if not leads:
        return "no_leads"
    threshold = 0.85 if enriched else 0.70
    with_email = sum(1 for l in leads if l.get("email"))
    pct = with_email / len(leads)
    if pct < threshold:
        return f"email_coverage {pct:.0%} < {threshold:.0%} ({with_email}/{len(leads)})"
    return None


def _gate_email_validity(leads: list[dict]) -> Optional[str]:
    """Check that zero emails match known-invalid patterns."""
    invalid = [
        l.get("email") for l in leads
        if l.get("email") and is_invalid_email(l["email"])
    ]
    if invalid:
        return f"invalid_emails: {len(invalid)} found ({', '.join(invalid[:3])})"
    return None


def _gate_email_verified(leads: list[dict], enriched: bool) -> Optional[str]:
    """For enriched packs: >= 30% of emails must be verified."""
    if not enriched:
        return None
    emails = [l for l in leads if l.get("email")]
    if not emails:
        return "email_verified: no emails to verify"
    verified = sum(1 for l in emails if l.get("email_verified"))
    pct = verified / len(emails)
    if pct < 0.30:
        return f"email_verified {pct:.0%} < 30% ({verified}/{len(emails)})"
    return None


def _gate_phone_coverage(leads: list[dict], enriched: bool) -> Optional[str]:
    """Check % of leads with phone."""
    if not leads:
        return "no_leads"
    threshold = 0.85 if enriched else 0.75
    with_phone = sum(1 for l in leads if l.get("phone"))
    pct = with_phone / len(leads)
    if pct < threshold:
        return f"phone_coverage {pct:.0%} < {threshold:.0%} ({with_phone}/{len(leads)})"
    return None


def _gate_website_coverage(leads: list[dict]) -> Optional[str]:
    """Check >= 60% of leads have a website."""
    if not leads:
        return "no_leads"
    with_website = sum(1 for l in leads if l.get("website"))
    pct = with_website / len(leads)
    if pct < 0.60:
        return f"website_coverage {pct:.0%} < 60% ({with_website}/{len(leads)})"
    return None


def _gate_deduplication(leads: list[dict]) -> Optional[str]:
    """Check zero duplicate dedup_keys within the pack."""
    keys = []
    for l in leads:
        key = l.get("dedup_key") or l.get("name_normalized", "")
        keys.append(key)
    unique = set(keys)
    if len(keys) != len(unique):
        dups = len(keys) - len(unique)
        return f"duplicates_in_pack: {dups}"
    return None


def _gate_pack_fill(leads: list[dict], target_count: int) -> Optional[str]:
    """Pack must contain >= 80% of target count."""
    if target_count <= 0:
        return None
    min_count = int(target_count * 0.80)
    if len(leads) < min_count:
        return f"underfilled: {len(leads)}/{target_count} (min {min_count})"
    return None


def _gate_freshness_days(leads: list[dict], max_days: int = 90) -> Optional[str]:
    """All leads must have data_freshness_days <= max_days."""
    stale = [
        l for l in leads
        if (l.get("data_freshness_days") or 0) > max_days
    ]
    if stale:
        return f"stale_leads: {len(stale)} older than {max_days} days"
    return None


def _gate_score_distribution(leads: list[dict]) -> Optional[str]:
    """Avg needs_score >= 15 and >= 20% of leads have score >= 30."""
    if not leads:
        return "no_leads"
    scores = [l.get("needs_score", 0) for l in leads]
    avg = sum(scores) / len(scores)
    if avg < 15:
        return f"avg_needs_score {avg:.1f} < 15"
    high_pct = sum(1 for s in scores if s >= 30) / len(scores)
    if high_pct < 0.20:
        return f"high_score_pct {high_pct:.0%} < 20%"
    return None


# ---------------------------------------------------------------------------
# Top-level gate runner
# ---------------------------------------------------------------------------

def check_quality_gates(
    leads: list[dict],
    target_count: int = 0,
    enriched: bool = False,
    max_freshness_days: int = 90,
) -> tuple[bool, list[str]]:
    """Run all quality gates on a list of lead dicts.

    Args:
        leads: List of verified lead dicts (from Supabase or pipeline models).
        target_count: Expected pack size (0 = skip fill check).
        enriched: Whether this is an enriched-tier pack.
        max_freshness_days: Maximum acceptable data age.

    Returns:
        (passed: bool, failures: list[str])
        A pack is sellable only when passed is True and failures is empty.
    """
    failures = []

    gates = [
        _gate_email_coverage(leads, enriched),
        _gate_email_validity(leads),
        _gate_email_verified(leads, enriched),
        _gate_phone_coverage(leads, enriched),
        _gate_website_coverage(leads),
        _gate_deduplication(leads),
        _gate_pack_fill(leads, target_count),
        _gate_freshness_days(leads, max_freshness_days),
        _gate_score_distribution(leads),
    ]

    for result in gates:
        if result is not None:
            failures.append(result)

    return (len(failures) == 0, failures)
