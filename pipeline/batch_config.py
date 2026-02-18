"""YAML batch config loader for pipeline runs.

A batch config describes what the pipeline should do: sweep a city,
run a verify pass, assemble packs, etc.
"""

from dataclasses import dataclass, field
from typing import Optional

import yaml


VALID_BATCH_TYPES = frozenset({
    "city_sweep",
    "signal_sweep",
    "verify_pass",
    "pack_assembly",
})


@dataclass
class BatchConfig:
    """Configuration for a single pipeline batch run."""

    batch_type: str
    city: str
    state: Optional[str] = None
    country: str = "US"
    niche: Optional[str] = None
    query: Optional[str] = None
    limit: int = 50
    enrichment_tier: str = "basic"
    sources: list[str] = field(default_factory=lambda: ["google_places"])
    max_freshness_days: int = 90

    def __post_init__(self):
        if self.batch_type not in VALID_BATCH_TYPES:
            raise ValueError(
                f"Invalid batch_type '{self.batch_type}'. "
                f"Must be one of: {sorted(VALID_BATCH_TYPES)}"
            )
        if not self.city:
            raise ValueError("city is required")


def load_batch_config(path: str) -> BatchConfig:
    """Load a batch config from a YAML file.

    Raises ValueError on invalid config, FileNotFoundError if missing.
    """
    with open(path, "r") as f:
        raw = yaml.safe_load(f)

    if not isinstance(raw, dict):
        raise ValueError(f"Invalid batch config: expected a YAML mapping, got {type(raw).__name__}")

    return BatchConfig(
        batch_type=raw.get("batch_type", ""),
        city=raw.get("city", ""),
        state=raw.get("state"),
        country=raw.get("country", "US"),
        niche=raw.get("niche"),
        query=raw.get("query"),
        limit=raw.get("limit", 50),
        enrichment_tier=raw.get("enrichment_tier", "basic"),
        sources=raw.get("sources", ["google_places"]),
        max_freshness_days=raw.get("max_freshness_days", 90),
    )
