import argparse
import logging
import sys
from pathlib import Path

from leadgen.generator import generate_pack, make_pack_id
from leadgen.paths import build_pack_paths, slugify
from leadgen.places import search_places

logger = logging.getLogger(__name__)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser()
    parser.add_argument("--query", "-q", required=True)
    parser.add_argument("--output", "-o", default=None)
    parser.add_argument("--limit", type=int, default=20)
    parser.add_argument("--jsonl-output", default=None)
    parser.add_argument("--country", default="USA")
    parser.add_argument("--state", default=None)
    parser.add_argument("--county", default=None)
    parser.add_argument("--city", default=None)
    parser.add_argument("--niche", default=None)
    parser.add_argument("--enriched", action="store_true", help="Generate enriched pack (default basic)")
    return parser


def run_cli(argv: list[str]) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    try:
        logger.info("Searching for leads for query '%s'...", args.query)
        businesses, status = search_places(args.query, args.limit, include_status=True)

        if status and status not in ("OK", "ZERO_RESULTS"):
            logger.warning("Google Places API returned status '%s'", status)

        if not businesses:
            print(f"No leads found for query '{args.query}'.")
            return 0

        output_path = args.output
        jsonl_output = args.jsonl_output
        pack_mode = False
        pack_id = make_pack_id(
            args.country,
            args.state,
            args.county,
            args.city,
            args.niche,
            args.limit,
        )

        # Precedence: explicit --output / --jsonl-output win.
        if output_path is None:
            if args.country and args.city:
                pack_mode = True
                # Use slugified query as basename; fallback to "leads" if empty
                basename = slugify(args.query) or "leads"
                csv_path, jsonl_path = build_pack_paths(
                    base_dir=Path("data/packs"),
                    country=args.country,
                    state=args.state,
                    county=args.county,
                    city=args.city,
                    niche=args.niche,
                    default_basename=basename,
                )
                output_path = str(csv_path)
                if jsonl_output is None:
                    jsonl_output = str(jsonl_path)
            else:
                output_path = "data/outputs/leads.csv"

        # Ensure parent directories exist for outputs we will write.
        Path(output_path).parent.mkdir(parents=True, exist_ok=True)
        if jsonl_output:
            Path(jsonl_output).parent.mkdir(parents=True, exist_ok=True)

        enrichment_tier = "enriched" if args.enriched else "basic"

        summary = generate_pack(
            query=args.query,
            country=args.country,
            state=args.state,
            county=args.county,
            city=args.city,
            niche=args.niche,
            limit=args.limit,
            pack_id=pack_id,
            base_dir=Path("data/packs"),
            output_csv=Path(output_path),
            output_jsonl=Path(jsonl_output) if jsonl_output else None,
            businesses=businesses,
            status=status,
            enrichment_tier=enrichment_tier,
        )

        logger.info("Exported %d leads to %s", summary["lead_count"], summary["csv_path"])
        return 0
    except Exception as exc:  # pragma: no cover - defensive guard
        logger.error("Unexpected error: %s", exc)
        return 1


def main() -> int:
    logging.basicConfig(level=logging.INFO)
    return run_cli(sys.argv[1:])


if __name__ == "__main__":
    raise SystemExit(main())
