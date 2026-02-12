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
