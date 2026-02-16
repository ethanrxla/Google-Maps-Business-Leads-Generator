#!/usr/bin/env python3
"""High-priority CSV -> Supabase backfill with mapping + audit logs.

Non-destructive: inserts only. No drops/truncates.
"""

from __future__ import annotations

import csv
import json
import re
import sys
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

PROJECT_ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(PROJECT_ROOT))

from db.supabase_client import get_client  # noqa: E402

PIPELINE_CSV = Path("/home/ethan/.openclaw/workspace/leads/lead_pipeline_enriched.csv")
VERIFIED_CSV = Path("/home/ethan/.openclaw/workspace/leads/lead_verified.csv")

ALLOWED_STATUS = {"new", "deduped", "sent_to_verify", "invalid", "duplicate"}
PATCH_FIELDS = ("address", "city", "phone", "email", "website")
CANDIDATE_FIELD_FALLBACKS = {
    "address": ("address",),
    "city": ("city",),
    "phone": ("phone_raw", "phone"),
    "email": ("email_raw", "email"),
    "website": ("website",),
}


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def normalize_slug(text: str) -> str:
    text = (text or "").strip().lower()
    text = re.sub(r"[^a-z0-9]+", "-", text)
    text = re.sub(r"-+", "-", text).strip("-")
    return text


def dedupe_key(name_normalized: str, website: str | None) -> tuple[str, str]:
    return ((name_normalized or "").strip().lower(), (website or "").strip().lower())


def _fetch_existing_key_set(client, table: str) -> set[tuple[str, str]]:
    keys: set[tuple[str, str]] = set()
    start = 0
    page_size = 1000
    while True:
        rows = (
            client.table(table)
            .select("name_normalized,website")
            .range(start, start + page_size - 1)
            .execute()
            .data
            or []
        )
        for row in rows:
            keys.add(dedupe_key(row.get("name_normalized") or "", row.get("website")))
        if len(rows) < page_size:
            break
        start += page_size
    return keys


def map_source(raw: str) -> tuple[str, str | None]:
    s = (raw or "").strip().lower()
    if not s:
        return "manual", "source_blank_defaulted_manual"
    if "google" in s or "maps" in s or "places" in s:
        return "google_places", None
    if "harvester" in s:
        return "theharvester", None
    if "serp" in s or "search" in s or s in {"x search", "twitter search"}:
        return "serp", None
    if "html" in s or "scrape" in s or "crawl" in s:
        return "html_scrape", None
    if "manual" in s:
        return "manual", None
    return "manual", f"source_unmapped_defaulted_manual:{raw}"


def map_status(raw: str) -> tuple[str, str | None]:
    s = (raw or "").strip().lower()
    if s in ALLOWED_STATUS:
        return s, None
    if s in {"qualified", "verified", "ready", "contacted"}:
        return "sent_to_verify", f"status_mapped:{s}->sent_to_verify"
    if s in {"", "new_lead", "open"}:
        return "new", f"status_defaulted_new:{s or 'blank'}"
    return "new", f"status_unmapped_defaulted_new:{s}"


def _clean_optional_text(value: Any) -> str | None:
    if value is None:
        return None
    text = str(value).strip()
    return text or None


def _coverage_counts(row: dict[str, Any]) -> dict[str, int]:
    return {field: int(_clean_optional_text(row.get(field)) is not None) for field in PATCH_FIELDS}


def _coverage_percentages(coverage_counts: Counter, total_rows: int) -> dict[str, float]:
    if total_rows <= 0:
        return {field: 0.0 for field in PATCH_FIELDS}
    return {
        field: round((coverage_counts[field] / total_rows) * 100, 2)
        for field in PATCH_FIELDS
    }


def enrich_verified_row_from_candidates(
    verified_row: dict[str, Any],
    candidate_rows: list[dict[str, Any]],
) -> tuple[dict[str, Any], list[str]]:
    """Fill missing verified fields from linked candidates in deterministic order.

    Rules:
    - Never overwrite non-empty verified row values.
    - Field order is fixed by PATCH_FIELDS.
    - Candidate order is fixed by input order (typically candidate_ids order).
    """
    patched = dict(verified_row)
    updated_fields: list[str] = []

    for field in PATCH_FIELDS:
        if _clean_optional_text(patched.get(field)) is not None:
            continue

        for candidate in candidate_rows:
            for source_field in CANDIDATE_FIELD_FALLBACKS[field]:
                candidate_val = _clean_optional_text(candidate.get(source_field))
                if candidate_val is not None:
                    patched[field] = candidate_val
                    updated_fields.append(field)
                    break
            if field in updated_fields:
                break

    return patched, updated_fields


def create_batch_run(client, batch_type: str, config: dict[str, Any]) -> str:
    res = client.table("batch_runs").insert({
        "batch_type": batch_type,
        "config": config,
        "status": "running",
        "started_at": now_iso(),
    }).execute()
    return res.data[0]["id"]


def log_event(client, batch_id: str, event_type: str, payload: dict[str, Any]) -> None:
    client.table("pipeline_events").insert({
        "batch_id": batch_id,
        "event_type": event_type,
        "payload": payload,
    }).execute()


def finalize_batch(client, batch_id: str, status: str, stats: dict[str, Any], error_message: str | None = None) -> None:
    updates: dict[str, Any] = {
        "status": status,
        "completed_at": now_iso(),
        "stats": stats,
    }
    if error_message:
        updates["error_message"] = error_message
    client.table("batch_runs").update(updates).eq("id", batch_id).execute()


def run() -> dict[str, Any]:
    client = get_client()
    candidate_ids_by_name = defaultdict(list)
    report: dict[str, Any] = {"candidates": {}, "verified_leads": {}}

    # Prevent duplicate growth across repeated backfill runs.
    existing_candidate_keys = _fetch_existing_key_set(client, "candidates")
    existing_verified_keys = _fetch_existing_key_set(client, "verified_leads")

    cand_batch_id = create_batch_run(client, "city_sweep", {"job": "csv_backfill_candidates", "file": str(PIPELINE_CSV)})
    log_event(client, cand_batch_id, "import_started", {"table": "candidates", "file": str(PIPELINE_CSV)})

    cand_reason_counts = Counter()
    cand_inserted = 0
    cand_rejected = 0

    try:
        with PIPELINE_CSV.open("r", encoding="utf-8", newline="") as f:
            reader = csv.DictReader(f)
            for idx, row in enumerate(reader, start=2):
                lead_name = (row.get("lead_name") or "").strip()
                if not lead_name:
                    cand_rejected += 1
                    cand_reason_counts["missing_lead_name"] += 1
                    continue

                source, source_reason = map_source(row.get("source", ""))
                status, status_reason = map_status(row.get("status", ""))
                name_normalized = normalize_slug(lead_name)

                mapped = {
                    "name": lead_name,
                    "name_normalized": name_normalized,
                    "website": (row.get("website_url") or "").strip() or None,
                    "source": source,
                    "status": status,
                    "collection_batch_id": cand_batch_id,
                    "collected_at": (row.get("created_at") or "").strip() or now_iso(),
                    "has_website": bool((row.get("website_url") or "").strip()),
                    "raw_data": row,
                }

                if set(row.keys()) - {"lead_name", "website_url", "source", "status"}:
                    cand_reason_counts["unmatched_fields_to_raw_data"] += 1
                if source_reason:
                    cand_reason_counts[source_reason] += 1
                if status_reason:
                    cand_reason_counts[status_reason] += 1

                key = dedupe_key(name_normalized, mapped["website"])
                if key in existing_candidate_keys:
                    cand_reason_counts["duplicate_key_skipped"] += 1
                    continue

                try:
                    ins = client.table("candidates").insert(mapped).execute().data[0]
                    cand_inserted += 1
                    existing_candidate_keys.add(key)
                    candidate_ids_by_name[name_normalized].append(ins["id"])
                except Exception as e:
                    cand_rejected += 1
                    cand_reason_counts[f"insert_error:{type(e).__name__}"] += 1
                    log_event(client, cand_batch_id, "import_row_error", {"table": "candidates", "row": idx, "lead_name": lead_name, "error": str(e)})

        cand_stats = {
            "file": str(PIPELINE_CSV),
            "inserted": cand_inserted,
            "skipped": 0,
            "rejected": cand_rejected,
            "reason_breakdown": dict(cand_reason_counts),
        }
        log_event(client, cand_batch_id, "import_completed", {"table": "candidates", **cand_stats})
        finalize_batch(client, cand_batch_id, "completed", cand_stats)
        report["candidates"] = {"batch_id": cand_batch_id, **cand_stats}
    except Exception as e:
        log_event(client, cand_batch_id, "import_error", {"table": "candidates", "error": str(e)})
        finalize_batch(client, cand_batch_id, "error", {"inserted": cand_inserted, "rejected": cand_rejected, "reason_breakdown": dict(cand_reason_counts)}, error_message=str(e))
        raise

    ver_batch_id = create_batch_run(client, "verify_pass", {"job": "csv_backfill_verified_leads", "file": str(VERIFIED_CSV), "candidate_batch_id": cand_batch_id})
    log_event(client, ver_batch_id, "import_started", {"table": "verified_leads", "file": str(VERIFIED_CSV)})

    ver_reason_counts = Counter()
    ver_inserted = 0
    ver_rejected = 0
    ver_patch_updates = Counter()
    ver_patch_before_coverage = Counter()
    ver_patch_after_coverage = Counter()
    candidate_cache: dict[str, dict[str, Any] | None] = {}

    try:
        with VERIFIED_CSV.open("r", encoding="utf-8", newline="") as f:
            reader = csv.DictReader(f)
            for idx, row in enumerate(reader, start=2):
                lead_name = (row.get("lead_name") or row.get("name") or "").strip()
                if not lead_name:
                    ver_rejected += 1
                    ver_reason_counts["missing_lead_name"] += 1
                    continue

                name_normalized = normalize_slug(lead_name)
                candidate_ids = list(dict.fromkeys(candidate_ids_by_name.get(name_normalized, [])))
                if not candidate_ids:
                    db_rows = client.table("candidates").select("id").eq("name_normalized", name_normalized).execute().data
                    # Keep deterministic order for enrichment patching when candidate_ids
                    # are sourced from DB lookups instead of in-memory insert order.
                    candidate_ids = sorted(r["id"] for r in db_rows)
                if not candidate_ids:
                    candidate_source, _ = map_source(row.get("source_method", "") or row.get("source", ""))
                    cand_ins = client.table("candidates").insert({
                        "name": lead_name,
                        "name_normalized": name_normalized,
                        "address": (row.get("address") or "").strip() or None,
                        "city": (row.get("city") or "").strip() or None,
                        "phone_raw": (row.get("phone") or "").strip() or None,
                        "email_raw": (row.get("email") or "").strip() or None,
                        "website": (row.get("website") or row.get("resolved_website_url") or row.get("source_url") or "").strip() or None,
                        "source": candidate_source,
                        "status": "sent_to_verify",
                        "collection_batch_id": cand_batch_id,
                        "raw_data": row,
                        "has_website": bool((row.get("website") or row.get("resolved_website_url") or "").strip()),
                    }).execute().data[0]
                    candidate_ids = [cand_ins["id"]]
                    ver_reason_counts["autocreated_candidate_for_verified_row"] += 1

                candidate_rows: list[dict[str, Any]] = []
                for candidate_id in candidate_ids:
                    if candidate_id not in candidate_cache:
                        fetched = client.table("candidates").select("id,address,city,phone_raw,email_raw,website").eq("id", candidate_id).limit(1).execute().data
                        candidate_cache[candidate_id] = fetched[0] if fetched else None
                    cached = candidate_cache.get(candidate_id)
                    if cached:
                        candidate_rows.append(cached)

                source, source_reason = map_source(row.get("source_method", "") or row.get("source", ""))
                status, status_reason = map_status(row.get("verification_status", "") or row.get("status", ""))
                try:
                    needs_score = max(0, min(100, int((row.get("total_score") or "0").strip() or 0) * 5))
                except ValueError:
                    needs_score = 0
                    ver_reason_counts["total_score_non_numeric_defaulted_0"] += 1

                website_val = (row.get("website") or row.get("resolved_website_url") or row.get("source_url") or "").strip() or None

                mapped = {
                    "candidate_ids": candidate_ids,
                    "name": lead_name,
                    "name_normalized": name_normalized,
                    "address": (row.get("address") or "").strip() or None,
                    "city": (row.get("city") or "").strip() or None,
                    "phone": (row.get("phone") or "").strip() or None,
                    "email": (row.get("email") or "").strip() or None,
                    "website": website_val,
                    "needs_score": needs_score,
                    "lead_quality_score": needs_score,
                    "verification_batch_id": ver_batch_id,
                    "verification_sources": [source],
                    "provenance": {
                        "source_csv": str(VERIFIED_CSV),
                        "source_row": idx,
                        "verification_status": row.get("verification_status"),
                        "source_method": row.get("source_method"),
                        "source_url": row.get("source_url"),
                        "mapped_source": source,
                        "mapped_status": status,
                        "imported_at": now_iso(),
                    },
                    "has_website": bool(website_val),
                    "needs_website": not bool(website_val),
                    "email_verified": status == "sent_to_verify" and bool((row.get("email") or "").strip()),
                    "phone_verified": status == "sent_to_verify" and bool((row.get("phone") or "").strip()),
                }

                before_cov = _coverage_counts(mapped)
                mapped, updated_fields = enrich_verified_row_from_candidates(mapped, candidate_rows)
                after_cov = _coverage_counts(mapped)
                for field in PATCH_FIELDS:
                    ver_patch_before_coverage[field] += before_cov[field]
                    ver_patch_after_coverage[field] += after_cov[field]
                for field in updated_fields:
                    ver_patch_updates[field] += 1

                if source_reason:
                    ver_reason_counts[source_reason] += 1
                if status_reason:
                    ver_reason_counts[status_reason] += 1
                if (row.get("verification_status") or "").strip().lower() != "verified":
                    ver_reason_counts["verification_status_not_verified"] += 1

                verified_key = dedupe_key(name_normalized, mapped["website"])
                if verified_key in existing_verified_keys:
                    ver_reason_counts["duplicate_key_skipped"] += 1
                    continue

                try:
                    client.table("verified_leads").insert(mapped).execute()
                    ver_inserted += 1
                    existing_verified_keys.add(verified_key)
                except Exception as e:
                    ver_rejected += 1
                    ver_reason_counts[f"insert_error:{type(e).__name__}"] += 1
                    log_event(client, ver_batch_id, "import_row_error", {"table": "verified_leads", "row": idx, "lead_name": lead_name, "error": str(e)})

        coverage_before_pct = _coverage_percentages(ver_patch_before_coverage, ver_inserted)
        coverage_after_pct = _coverage_percentages(ver_patch_after_coverage, ver_inserted)

        ver_stats = {
            "file": str(VERIFIED_CSV),
            "inserted": ver_inserted,
            "skipped": 0,
            "rejected": ver_rejected,
            "reason_breakdown": dict(ver_reason_counts),
            "verified_enrichment_patch": {
                "fields_order": list(PATCH_FIELDS),
                "updated_counts_by_field": {
                    field: int(ver_patch_updates[field]) for field in PATCH_FIELDS
                },
                "coverage_before_pct": coverage_before_pct,
                "coverage_after_pct": coverage_after_pct,
            },
        }
        log_event(client, ver_batch_id, "import_completed", {"table": "verified_leads", **ver_stats})
        finalize_batch(client, ver_batch_id, "completed", ver_stats)
        report["verified_leads"] = {"batch_id": ver_batch_id, **ver_stats}
    except Exception as e:
        log_event(client, ver_batch_id, "import_error", {"table": "verified_leads", "error": str(e)})
        finalize_batch(client, ver_batch_id, "error", {"inserted": ver_inserted, "rejected": ver_rejected, "reason_breakdown": dict(ver_reason_counts)}, error_message=str(e))
        raise

    return report


if __name__ == "__main__":
    print(json.dumps(run(), indent=2, sort_keys=True))
