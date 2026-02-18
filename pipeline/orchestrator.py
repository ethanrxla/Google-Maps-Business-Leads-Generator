"""Pipeline orchestrator: runs the full collect → dedupe → verify → assemble flow.

Each stage logs a pipeline event and the batch_run status is updated
at each transition. On error, the batch is marked "error" and the
exception is captured in the event payload.

CLI usage::

    python -m pipeline.orchestrator --config batches/city_sweep_example.yaml
    python -m pipeline --config batches/city_sweep_example.yaml
"""

import argparse
import json
import logging
import sys
from typing import Optional

from db.repositories import (
    create_batch_run,
    insert_candidates_batch,
    insert_verified_leads_batch,
    insert_pack,
    insert_pack_entries_batch,
    log_pipeline_event,
    update_batch_run,
)
from pipeline.batch_config import load_batch_config
from pipeline.collector import collect_candidates
from pipeline.deduper import dedupe_candidates
from pipeline.pack_assembler import assemble_pack
from pipeline.verifier import verify_candidates

logger = logging.getLogger(__name__)


def run_batch(
    batch_type: str,
    query: str,
    city: str,
    state: Optional[str] = None,
    country: str = "US",
    niche: Optional[str] = None,
    limit: int = 50,
    enrichment_tier: str = "basic",
    hunter_client=None,
    apollo_client=None,
) -> dict:
    """Run a full pipeline batch.

    Flow: create_batch_run → collect → dedupe → verify → assemble → persist.

    Returns a summary dict with batch_id, status, and metrics.
    """
    # Create batch run
    config = {
        "batch_type": batch_type,
        "query": query,
        "city": city,
        "state": state,
        "country": country,
        "niche": niche,
        "limit": limit,
        "enrichment_tier": enrichment_tier,
    }
    batch_run = create_batch_run(batch_type, config=config)
    batch_id = batch_run["id"]

    try:
        update_batch_run(batch_id, {"status": "running"})

        # Stage 1: Collect
        log_pipeline_event(batch_id, "collect_start", {"query": query, "limit": limit})
        candidates, api_status = collect_candidates(
            query=query, limit=limit, batch_id=batch_id,
        )
        log_pipeline_event(batch_id, "collect_done", {
            "count": len(candidates),
            "api_status": api_status,
        })

        if not candidates:
            update_batch_run(batch_id, {"status": "completed"})
            log_pipeline_event(batch_id, "pipeline_done", {"reason": "no_candidates"})
            return {
                "batch_id": batch_id,
                "status": "completed",
                "candidates_collected": 0,
                "candidates_kept": 0,
                "verified_count": 0,
                "pack": None,
            }

        # Persist candidates
        inserted_candidates = insert_candidates_batch(candidates)

        # Stage 2: Dedupe
        log_pipeline_event(batch_id, "dedupe_start", {"count": len(inserted_candidates)})
        kept, dupes = dedupe_candidates(inserted_candidates)
        log_pipeline_event(batch_id, "dedupe_done", {
            "kept": len(kept),
            "duplicates": len(dupes),
        })

        # Stage 3: Verify
        log_pipeline_event(batch_id, "verify_start", {"count": len(kept)})
        verified = verify_candidates(
            kept,
            hunter_client=hunter_client,
            apollo_client=apollo_client,
            batch_id=batch_id,
        )
        log_pipeline_event(batch_id, "verify_done", {"count": len(verified)})

        # Persist verified leads
        if verified:
            insert_verified_leads_batch(verified)

        # Stage 4: Assemble
        log_pipeline_event(batch_id, "assemble_start", {"count": len(verified)})
        pack = assemble_pack(
            leads=verified,
            niche=niche or query,
            city=city,
            state=state,
            country=country,
            enrichment_tier=enrichment_tier,
            target_count=limit,
        )
        log_pipeline_event(batch_id, "assemble_done", {
            "sellable": pack["sellable"],
            "quality_gate_failures": pack["quality_gate_failures"],
        })

        # Persist pack
        insert_pack(pack)

        # Persist pack entries
        pack_entries = [
            {"pack_id": pack["pack_id"], "lead_id": lead.get("id")}
            for lead in verified
            if lead.get("id")
        ]
        if pack_entries:
            insert_pack_entries_batch(pack_entries)

        update_batch_run(batch_id, {"status": "completed"})
        log_pipeline_event(batch_id, "pipeline_done", {"pack_id": pack["pack_id"]})

        return {
            "batch_id": batch_id,
            "status": "completed",
            "candidates_collected": len(candidates),
            "candidates_kept": len(kept),
            "duplicates_removed": len(dupes),
            "verified_count": len(verified),
            "pack": pack,
        }

    except Exception as exc:
        logger.exception("Pipeline batch %s failed", batch_id)
        try:
            update_batch_run(batch_id, {"status": "error"})
            log_pipeline_event(batch_id, "pipeline_error", {
                "error": str(exc),
            })
        except Exception:
            logger.exception("Failed to update batch status to error")
        raise


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Run a pipeline batch from a YAML config file.",
    )
    parser.add_argument(
        "--config",
        required=True,
        help="Path to a batch YAML config file (e.g. batches/city_sweep_example.yaml)",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    """CLI entry point.  Returns 0 on success, 1 on error."""
    parser = build_parser()
    args = parser.parse_args(argv)

    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(name)s: %(message)s")

    cfg = load_batch_config(args.config)

    summary = run_batch(
        batch_type=cfg.batch_type,
        query=cfg.query or f"{cfg.niche} in {cfg.city} {cfg.state or ''}".strip(),
        city=cfg.city,
        state=cfg.state,
        country=cfg.country,
        niche=cfg.niche,
        limit=cfg.limit,
        enrichment_tier=cfg.enrichment_tier,
    )

    print(json.dumps(summary, indent=2, default=str))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
