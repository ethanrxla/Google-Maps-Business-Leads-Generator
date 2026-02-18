import re
from pathlib import Path
from typing import Optional, Tuple


def slugify(value: str) -> str:
    """
    Lowercase, trim, and replace non-alphanumeric sequences with single underscores.
    Example: "Boca Raton, FL" -> "boca_raton_fl"
    """
    value = value.strip().lower()
    # Replace any sequence of non-alphanumeric characters with underscore
    value = re.sub(r"[^a-z0-9]+", "_", value)
    return value.strip("_")


def build_pack_paths(
    base_dir: Path,
    country: Optional[str],
    state: Optional[str],
    county: Optional[str],
    city: Optional[str],
    niche: Optional[str],
    default_basename: str,
) -> Tuple[Path, Path]:
    """
    Construct CSV and JSONL output paths based on location metadata.

    Skips missing components gracefully; uses default_basename as filename stem.
    Does not create directories; callers should ensure parents exist.
    """
    parts = []
    for component in (country, state, county, city, niche):
        if component:
            slug = slugify(component)
            if slug:
                parts.append(slug)

    dir_path = base_dir
    if parts:
        dir_path = base_dir.joinpath(*parts)

    stem = default_basename or "leads"
    csv_path = dir_path / f"{stem}.csv"
    jsonl_path = dir_path / f"{stem}.jsonl"
    return csv_path, jsonl_path
