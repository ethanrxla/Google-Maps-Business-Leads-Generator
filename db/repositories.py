"""Repository functions for Supabase CRUD operations.

Thin wrappers around the Supabase client for candidates and batch_runs.
Each function handles one table concern. No business logic here.

All functions handle empty/no-row responses safely:
- Single-row getters return None when not found.
- Insert functions raise RepositoryError with context on failure.
- Update/delete functions return empty dict / False when target is missing.
"""

import logging
from typing import Any, Optional

from db.supabase_client import get_client
from pipeline.models import normalize_source

logger = logging.getLogger(__name__)


class RepositoryError(Exception):
    """Raised when a repository operation fails unexpectedly."""


def _safe_first(data: list, context: str) -> dict:
    """Extract first row from result.data, raising RepositoryError if empty."""
    if not data:
        raise RepositoryError(f"Insert returned no rows ({context})")
    return data[0]


# ---------------------------------------------------------------------------
# batch_runs
# ---------------------------------------------------------------------------

def create_batch_run(
    batch_type: str,
    config: Optional[dict] = None,
) -> dict:
    """Insert a new batch_run and return the row.

    Raises RepositoryError if the insert returns no data.
    """
    client = get_client()
    row = {
        "batch_type": batch_type,
        "config": config or {},
        "status": "pending",
    }
    result = client.table("batch_runs").insert(row).execute()
    return _safe_first(result.data, "batch_runs insert")


def update_batch_run(batch_id: str, updates: dict) -> Optional[dict]:
    """Update a batch_run by id. Returns the updated row or None if not found."""
    client = get_client()
    result = (
        client.table("batch_runs")
        .update(updates)
        .eq("id", batch_id)
        .execute()
    )
    if not result.data:
        logger.warning("update_batch_run: no row matched id=%s", batch_id)
        return None
    return result.data[0]


def get_batch_run(batch_id: str) -> Optional[dict]:
    """Fetch a single batch_run by id. Returns None if not found."""
    client = get_client()
    result = (
        client.table("batch_runs")
        .select("*")
        .eq("id", batch_id)
        .maybe_single()
        .execute()
    )
    return result.data


# ---------------------------------------------------------------------------
# candidates
# ---------------------------------------------------------------------------

VALID_SOURCES = frozenset({
    "google_places", "theharvester", "manual", "serp", "html_scrape",
})


def _validate_candidate(candidate: dict) -> None:
    """Validate required fields before insert. Raises RepositoryError."""
    for field in ("name", "name_normalized", "source"):
        if not candidate.get(field):
            raise RepositoryError(
                f"Candidate missing required field: {field}"
            )
    candidate["source"] = normalize_source(candidate["source"])
    src = candidate["source"]
    if src not in VALID_SOURCES:
        raise RepositoryError(
            f"Invalid source '{src}'. Must be one of: {sorted(VALID_SOURCES)}"
        )


def insert_candidate(candidate: dict) -> dict:
    """Insert a single candidate row. Returns the inserted row.

    Validates required fields (name, name_normalized, source) and source enum.
    Raises RepositoryError if validation fails or insert returns no data.
    """
    _validate_candidate(candidate)
    client = get_client()
    result = client.table("candidates").insert(candidate).execute()
    return _safe_first(result.data, f"candidates insert name={candidate.get('name', '?')}")


def insert_candidates_batch(candidates: list[dict]) -> list[dict]:
    """Insert multiple candidates in one request. Returns inserted rows.

    Validates each candidate before insert.
    Raises RepositoryError if any candidate is invalid or insert returns no data.
    """
    if not candidates:
        return []
    for i, c in enumerate(candidates):
        try:
            _validate_candidate(c)
        except RepositoryError as e:
            raise RepositoryError(f"Candidate at index {i}: {e}") from e
    client = get_client()
    result = client.table("candidates").insert(candidates).execute()
    if not result.data:
        raise RepositoryError(
            f"Batch insert returned no rows ({len(candidates)} candidates submitted)"
        )
    return result.data


def get_candidates(
    status: Optional[str] = None,
    batch_id: Optional[str] = None,
    city_normalized: Optional[str] = None,
    limit: int = 1000,
    offset: int = 0,
) -> list[dict]:
    """Query candidates with optional filters. Returns list of rows (may be empty)."""
    client = get_client()
    query = client.table("candidates").select("*")

    if status is not None:
        query = query.eq("status", status)
    if batch_id is not None:
        query = query.eq("collection_batch_id", batch_id)
    if city_normalized is not None:
        query = query.eq("city_normalized", city_normalized)

    query = query.range(offset, offset + limit - 1)
    result = query.execute()
    return result.data or []


def get_candidate(candidate_id: str) -> Optional[dict]:
    """Fetch a single candidate by id. Returns None if not found."""
    client = get_client()
    result = (
        client.table("candidates")
        .select("*")
        .eq("id", candidate_id)
        .maybe_single()
        .execute()
    )
    return result.data


def update_candidate(candidate_id: str, updates: dict) -> Optional[dict]:
    """Update a candidate by id. Returns the updated row or None if not found."""
    client = get_client()
    result = (
        client.table("candidates")
        .update(updates)
        .eq("id", candidate_id)
        .execute()
    )
    if not result.data:
        logger.warning("update_candidate: no row matched id=%s", candidate_id)
        return None
    return result.data[0]


def delete_candidate(candidate_id: str) -> bool:
    """Delete a candidate by id. Returns True if deleted, False otherwise."""
    client = get_client()
    result = (
        client.table("candidates")
        .delete()
        .eq("id", candidate_id)
        .execute()
    )
    return bool(result.data)


def count_candidates(status: Optional[str] = None) -> int:
    """Count candidates, optionally filtered by status."""
    client = get_client()
    query = client.table("candidates").select("id", count="exact")
    if status is not None:
        query = query.eq("status", status)
    result = query.execute()
    return result.count or 0


# ---------------------------------------------------------------------------
# verified_leads
# ---------------------------------------------------------------------------

def insert_verified_lead(lead: dict) -> dict:
    """Insert a single verified lead. Returns the inserted row."""
    for field in ("name", "name_normalized"):
        if not lead.get(field):
            raise RepositoryError(f"Verified lead missing required field: {field}")
    client = get_client()
    result = client.table("verified_leads").insert(lead).execute()
    return _safe_first(result.data, f"verified_leads insert name={lead.get('name', '?')}")


def insert_verified_leads_batch(leads: list[dict]) -> list[dict]:
    """Insert multiple verified leads in one request."""
    if not leads:
        return []
    for i, lead in enumerate(leads):
        for field in ("name", "name_normalized"):
            if not lead.get(field):
                raise RepositoryError(
                    f"Verified lead at index {i} missing required field: {field}"
                )
    client = get_client()
    result = client.table("verified_leads").insert(leads).execute()
    if not result.data:
        raise RepositoryError(
            f"Batch insert returned no rows ({len(leads)} verified leads submitted)"
        )
    return result.data


def get_verified_leads(
    city: Optional[str] = None,
    batch_id: Optional[str] = None,
    min_quality_score: Optional[int] = None,
    limit: int = 1000,
    offset: int = 0,
) -> list[dict]:
    """Query verified leads with optional filters."""
    client = get_client()
    query = client.table("verified_leads").select("*")
    if city is not None:
        query = query.eq("city", city)
    if batch_id is not None:
        query = query.eq("verification_batch_id", batch_id)
    if min_quality_score is not None:
        query = query.gte("lead_quality_score", min_quality_score)
    query = query.range(offset, offset + limit - 1)
    result = query.execute()
    return result.data or []


def get_verified_lead(lead_id: str) -> Optional[dict]:
    """Fetch a single verified lead by id."""
    client = get_client()
    result = (
        client.table("verified_leads")
        .select("*")
        .eq("id", lead_id)
        .maybe_single()
        .execute()
    )
    return result.data


def update_verified_lead(lead_id: str, updates: dict) -> Optional[dict]:
    """Update a verified lead by id."""
    client = get_client()
    result = (
        client.table("verified_leads")
        .update(updates)
        .eq("id", lead_id)
        .execute()
    )
    if not result.data:
        logger.warning("update_verified_lead: no row matched id=%s", lead_id)
        return None
    return result.data[0]


def count_verified_leads(batch_id: Optional[str] = None) -> int:
    """Count verified leads, optionally filtered by batch_id."""
    client = get_client()
    query = client.table("verified_leads").select("id", count="exact")
    if batch_id is not None:
        query = query.eq("verification_batch_id", batch_id)
    result = query.execute()
    return result.count or 0


# ---------------------------------------------------------------------------
# packs
# ---------------------------------------------------------------------------

def insert_pack(pack: dict) -> dict:
    """Insert a new pack. Returns the inserted row."""
    if not pack.get("pack_id"):
        raise RepositoryError("Pack missing required field: pack_id")
    client = get_client()
    result = client.table("packs").insert(pack).execute()
    return _safe_first(result.data, f"packs insert pack_id={pack.get('pack_id', '?')}")


def get_pack(pack_id: str) -> Optional[dict]:
    """Fetch a single pack by pack_id."""
    client = get_client()
    result = (
        client.table("packs")
        .select("*")
        .eq("pack_id", pack_id)
        .maybe_single()
        .execute()
    )
    return result.data


def get_sellable_packs(limit: int = 100) -> list[dict]:
    """Fetch packs where sellable=true."""
    client = get_client()
    result = (
        client.table("packs")
        .select("*")
        .eq("sellable", True)
        .limit(limit)
        .execute()
    )
    return result.data or []


def update_pack(pack_id: str, updates: dict) -> Optional[dict]:
    """Update a pack by pack_id."""
    client = get_client()
    result = (
        client.table("packs")
        .update(updates)
        .eq("pack_id", pack_id)
        .execute()
    )
    if not result.data:
        logger.warning("update_pack: no row matched pack_id=%s", pack_id)
        return None
    return result.data[0]


# ---------------------------------------------------------------------------
# pack_entries
# ---------------------------------------------------------------------------

def insert_pack_entries_batch(entries: list[dict]) -> list[dict]:
    """Insert multiple pack entries in one request."""
    if not entries:
        return []
    client = get_client()
    result = client.table("pack_entries").insert(entries).execute()
    if not result.data:
        raise RepositoryError(
            f"Batch insert returned no rows ({len(entries)} pack entries submitted)"
        )
    return result.data


def get_pack_entries(pack_id: str) -> list[dict]:
    """Fetch all entries for a pack."""
    client = get_client()
    result = (
        client.table("pack_entries")
        .select("*")
        .eq("pack_id", pack_id)
        .execute()
    )
    return result.data or []


# ---------------------------------------------------------------------------
# pipeline_events
# ---------------------------------------------------------------------------

def log_pipeline_event(
    batch_id: str,
    event_type: str,
    payload: Optional[dict] = None,
) -> dict:
    """Log a pipeline event. Returns the inserted row."""
    client = get_client()
    row = {
        "batch_id": batch_id,
        "event_type": event_type,
        "payload": payload or {},
    }
    result = client.table("pipeline_events").insert(row).execute()
    return _safe_first(result.data, f"pipeline_events insert batch_id={batch_id}")


def get_pipeline_events(
    batch_id: str,
    event_type: Optional[str] = None,
    limit: int = 100,
) -> list[dict]:
    """Query pipeline events for a batch."""
    client = get_client()
    query = (
        client.table("pipeline_events")
        .select("*")
        .eq("batch_id", batch_id)
    )
    if event_type is not None:
        query = query.eq("event_type", event_type)
    query = query.limit(limit)
    result = query.execute()
    return result.data or []
