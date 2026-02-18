#!/usr/bin/env python3
"""
Simplified batch processor for WSL harvester.
"""

from pathlib import Path
from typing import List, Dict, Any

from core.wsl_harvester import run_harvest_job
from core.job_result import HarvestJobResult


def _load_domains(path: str) -> List[str]:
    domains = []
    with open(path, "r") as f:
        for line in f:
            domain = line.strip()
            if domain and not domain.startswith("#"):
                domains.append(domain)
    return domains


def run_batch_from_file(path: str, **harvester_options) -> List[HarvestJobResult]:
    output_base = Path(harvester_options.get("output_base") or Path("harvest_outputs"))
    sources = harvester_options.get("sources") or ["google", "bing"]
    limit = harvester_options.get("limit") or 500
    export_windows = harvester_options.get("export_windows", False)

    results = []
    for domain in _load_domains(path):
        res = run_harvest_job(
            domain=domain,
            sources=sources,
            limit=limit,
            output_base=output_base,
            export_windows=export_windows,
        )
        results.append(res)
    return results
