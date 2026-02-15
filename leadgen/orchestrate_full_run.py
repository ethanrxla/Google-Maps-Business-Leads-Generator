from __future__ import annotations

import argparse
import csv
import hashlib
import json
import logging
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import yaml

from leadgen.generator import generate_pack, make_pack_id
from leadgen.models import Business
from leadgen.places import search_places

logger = logging.getLogger(__name__)
SHARDS = ("A", "B", "C")


@dataclass
class Target:
    id: str
    query: str
    country: str = "USA"
    state: str | None = None
    county: str | None = None
    city: str | None = None
    niche: str | None = None
    limit: int = 20
    shard: str | None = None
    enabled: bool = True


@dataclass
class StageResult:
    target_id: str
    shard: str
    collected: int = 0
    verified_deduped: int = 0
    packed: int = 0
    sellable: bool | None = None
    quality_gate_failures: list[str] | None = None
    status: str = "ok"
    reason: str | None = None


def _load_manifest(path: Path) -> dict[str, Any]:
    with path.open("r", encoding="utf-8") as f:
        if path.suffix.lower() == ".json":
            return json.load(f)
        return yaml.safe_load(f)


def _normalize_target(raw: dict[str, Any]) -> Target:
    if "id" not in raw or "query" not in raw:
        raise ValueError("Each target requires id and query")
    return Target(
        id=str(raw["id"]),
        query=str(raw["query"]),
        country=str(raw.get("country") or "USA"),
        state=raw.get("state"),
        county=raw.get("county"),
        city=raw.get("city"),
        niche=raw.get("niche"),
        limit=int(raw.get("limit") or 20),
        shard=(str(raw.get("shard")).upper() if raw.get("shard") else None),
        enabled=bool(raw.get("enabled", True)),
    )


def _stable_shard(target_id: str) -> str:
    digest = hashlib.sha256(target_id.encode("utf-8")).hexdigest()
    return SHARDS[int(digest[:8], 16) % len(SHARDS)]


def _target_shard(t: Target) -> str:
    if t.shard in SHARDS:
        return t.shard
    return _stable_shard(t.id)


def _write_csv(path: Path, rows: list[dict[str, Any]], fields: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=fields)
        w.writeheader()
        for row in rows:
            w.writerow({k: row.get(k) for k in fields})


def _dedupe_businesses(businesses: list[Business]) -> list[Business]:
    seen: set[str] = set()
    output: list[Business] = []
    for b in businesses:
        parts = [
            (b.name or "").strip().lower(),
            (b.address or "").strip().lower(),
            (b.website or "").strip().lower(),
            (b.phone or "").strip().lower(),
        ]
        key = "|".join(parts)
        if not parts[0] or key in seen:
            continue
        seen.add(key)
        output.append(b)
    return output


def run_target(
    target: Target,
    shard: str,
    output_dir: Path,
    base_pack_dir: Path,
    dry_run: bool,
    timeout_seconds: int,
) -> StageResult:
    started = time.monotonic()
    result = StageResult(target_id=target.id, shard=shard)

    collect_csv = output_dir / "collect" / f"{target.id}.csv"
    verify_csv = output_dir / "verify_dedupe" / f"{target.id}.csv"

    if dry_run:
        result.status = "dry_run"
        return result

    businesses, status = search_places(target.query, target.limit, include_status=True)
    if status and status not in ("OK", "ZERO_RESULTS"):
        logger.warning("target=%s places status=%s", target.id, status)
    result.collected = len(businesses)
    _write_csv(
        collect_csv,
        [
            {
                "name": b.name,
                "address": b.address,
                "website": b.website,
                "phone": b.phone,
                "place_id": b.place_id,
            }
            for b in businesses
        ],
        ["name", "address", "website", "phone", "place_id"],
    )

    if time.monotonic() - started > timeout_seconds:
        result.status = "timeout"
        result.reason = "timeout_after_collect"
        return result

    deduped = _dedupe_businesses(businesses)
    result.verified_deduped = len(deduped)
    _write_csv(
        verify_csv,
        [
            {
                "name": b.name,
                "address": b.address,
                "website": b.website,
                "phone": b.phone,
                "place_id": b.place_id,
            }
            for b in deduped
        ],
        ["name", "address", "website", "phone", "place_id"],
    )

    if time.monotonic() - started > timeout_seconds:
        result.status = "timeout"
        result.reason = "timeout_after_verify_dedupe"
        return result

    pack_id = make_pack_id(
        target.country,
        target.state,
        target.county,
        target.city,
        target.niche,
        target.limit,
    )
    summary = generate_pack(
        query=target.query,
        country=target.country,
        state=target.state,
        county=target.county,
        city=target.city,
        niche=target.niche,
        limit=target.limit,
        pack_id=pack_id,
        base_dir=base_pack_dir,
        businesses=deduped,
        status="OK",
        enrichment_tier="basic",
    )
    result.packed = int(summary.get("lead_count") or 0)
    result.sellable = bool(summary.get("sellable", False))
    result.quality_gate_failures = sorted(
        str(reason) for reason in (summary.get("quality_gate_failures") or [])
    )
    return result


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(description="One-command orchestration: collect -> verify/dedupe -> pack")
    p.add_argument("--manifest", required=True, help="YAML/JSON manifest file")
    p.add_argument("--shard", choices=SHARDS, required=True, help="Worker shard")
    p.add_argument("--output-dir", default="tmp_runs/orchestrated", help="Run artifact directory")
    p.add_argument("--base-pack-dir", default="data/packs", help="Output pack directory")
    p.add_argument("--max-targets", type=int, default=10)
    p.add_argument("--timeout-seconds", type=int, default=900)
    p.add_argument("--dry-run", action="store_true")
    return p


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")

    manifest = _load_manifest(Path(args.manifest))
    raw_targets = manifest.get("targets") or []
    targets = [_normalize_target(t) for t in raw_targets if t.get("enabled", True)]
    selected = [t for t in targets if _target_shard(t) == args.shard][: args.max_targets]

    run_id = f"run_{int(time.time())}_{args.shard.lower()}"
    output_dir = Path(args.output_dir) / run_id

    results: list[StageResult] = []
    for t in selected:
        shard = _target_shard(t)
        logger.info("running target=%s shard=%s", t.id, shard)
        try:
            results.append(
                run_target(
                    target=t,
                    shard=shard,
                    output_dir=output_dir,
                    base_pack_dir=Path(args.base_pack_dir),
                    dry_run=args.dry_run,
                    timeout_seconds=args.timeout_seconds,
                )
            )
        except Exception as exc:  # pragma: no cover
            results.append(StageResult(target_id=t.id, shard=shard, status="error", reason=str(exc)))

    summary = {
        "run_id": run_id,
        "manifest": str(Path(args.manifest)),
        "shard": args.shard,
        "selected_count": len(selected),
        "selected_target_ids": [t.id for t in selected],
        "results": [r.__dict__ for r in results],
    }
    output_dir.mkdir(parents=True, exist_ok=True)
    summary_path = output_dir / "summary.json"
    summary_path.write_text(json.dumps(summary, indent=2), encoding="utf-8")
    logger.info("wrote summary: %s", summary_path)
    print(json.dumps(summary, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
