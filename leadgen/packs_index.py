import os
from pathlib import Path
from typing import Dict, Optional, Tuple


def build_packs_index(base_dir: Path = Path("data/packs")) -> Dict[str, Dict[str, Optional[Path]]]:
    """
    Build an index mapping pack_id -> {"csv": Path | None, "jsonl": Path | None}.
    Supports both path-like pack_ids (e.g., "usa/florida/boca_raton") and underscore
    identifiers (e.g., "usa_florida_boca_raton").
    """
    index: Dict[str, Dict[str, Optional[Path]]] = {}
    if not base_dir.exists():
        return index

    for root, _dirs, files in os.walk(base_dir):
        csv_files = [f for f in files if f.endswith(".csv")]
        for csv_file in csv_files:
            csv_path = Path(root) / csv_file
            jsonl_path = csv_path.with_suffix(".jsonl")
            rel_dir = Path(root).relative_to(base_dir)
            base_key = rel_dir.as_posix() if rel_dir.as_posix() != "." else csv_path.stem
            entry = {
                "csv": csv_path,
                "jsonl": jsonl_path if jsonl_path.exists() else None,
            }
            # Directory-based key (e.g., usa/florida/miami)
            index[base_key] = entry
            index.setdefault(base_key.replace("/", "_"), entry)
            # Filename-based key (pack_id.csv -> pack_id)
            stem_key = csv_path.stem
            index.setdefault(stem_key, entry)
            index.setdefault(stem_key.replace("/", "_"), entry)
    return index


def resolve_pack_files(pack_id: str, base_dir: Path = Path("data/packs")) -> Tuple[Optional[Path], Optional[Path]]:
    """
    Resolve pack_id to (csv_path, jsonl_path).
    """
    index = build_packs_index(base_dir)
    entry = index.get(pack_id) or index.get(pack_id.replace("_", "/"))
    if not entry:
        return None, None
    return entry.get("csv"), entry.get("jsonl")


def list_packs(base_dir: Path = Path("data/packs")):
    """
    Recursively scan base_dir for generated packs and return a list of
    dicts with pack_id and file paths.
    Only include entries where at least one of CSV/JSONL exists.
    """
    packs = []
    if not base_dir.exists():
        return packs

    seen = set()
    for root, _dirs, files in os.walk(base_dir):
        rel_dir = Path(root).relative_to(base_dir)
        # Determine base pack_id from directory path
        base_key = rel_dir.as_posix()
        pack_id_dir = base_key.replace("/", "_") if base_key and base_key != "." else None

        csv_files = [f for f in files if f.endswith(".csv")]
        for csv_file in csv_files:
            csv_path = Path(root) / csv_file
            jsonl_path = csv_path.with_suffix(".jsonl")

            pack_id = pack_id_dir or csv_path.stem
            if pack_id in seen:
                continue
            seen.add(pack_id)

            packs.append(
                {
                    "pack_id": pack_id,
                    "csv_path": str(csv_path),
                    "jsonl_path": str(jsonl_path) if jsonl_path.exists() else None,
                }
            )
    return packs
