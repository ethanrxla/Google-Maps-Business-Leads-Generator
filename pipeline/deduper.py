"""Candidate deduplication.

Provides deterministic dedupe key computation and batch deduplication.
A dedupe key is built from normalized name + one anchor (phone or website or city).
"""

import re


_SUFFIX_RE = re.compile(
    r"\b(llc|inc|corp|corporation|co|ltd|limited|llp|pllc|pc|dba)\b",
    re.IGNORECASE,
)


def normalize_name(name: str) -> str:
    """Lowercase, strip common business suffixes, collapse non-alnum to underscore."""
    if not name:
        return ""
    lowered = name.lower().strip()
    lowered = _SUFFIX_RE.sub("", lowered)
    # Collapse non-alphanumeric runs to a single underscore
    result = re.sub(r"[^a-z0-9]+", "_", lowered)
    return result.strip("_")


def compute_dedupe_key(
    name: str,
    city: str | None = None,
    state: str | None = None,
    phone: str | None = None,
    website: str | None = None,
) -> str:
    """Build a stable dedupe key from name + best available anchor.

    Priority: phone > website > city+state > name-only.
    """
    norm = normalize_name(name)
    if not norm:
        return ""

    # Pick the best anchor
    if phone:
        anchor = re.sub(r"[^0-9]+", "", phone)
    elif website:
        anchor = re.sub(r"https?://", "", website.lower()).rstrip("/")
    elif city:
        parts = [city.lower().strip()]
        if state:
            parts.append(state.lower().strip())
        anchor = "_".join(parts)
    else:
        anchor = ""

    if anchor:
        return f"{norm}|{anchor}"
    return norm


def dedupe_candidates(candidates: list[dict]) -> tuple[list[dict], list[dict]]:
    """Deduplicate a list of candidate dicts in-place.

    Sets `dedup_key` on every candidate. Marks duplicates with
    status='duplicate' and keeps with status='deduped'.

    Returns (kept, duplicates).
    """
    seen: dict[str, int] = {}  # dedup_key -> index in kept
    kept: list[dict] = []
    dupes: list[dict] = []

    for candidate in candidates:
        key = compute_dedupe_key(
            name=candidate.get("name", ""),
            city=candidate.get("city") or candidate.get("city_normalized"),
            state=candidate.get("state"),
            phone=candidate.get("phone_raw") or candidate.get("phone"),
            website=candidate.get("website"),
        )
        candidate["dedup_key"] = key

        if not key:
            # Can't dedupe without a key — keep it
            candidate["status"] = "deduped"
            kept.append(candidate)
            continue

        if key in seen:
            candidate["status"] = "duplicate"
            dupes.append(candidate)
        else:
            seen[key] = len(kept)
            candidate["status"] = "deduped"
            kept.append(candidate)

    return kept, dupes
