# Harvest Intelligence Module (v0.1)

WSL-friendly OSINT / lead intelligence harvester. Runs theHarvester (or stubs during tests) to collect domain intelligence and export structured results.

## Usage

Single-domain (CLI):
```bash
python3 -m harvest.src.core.wsl_harvester -d example.com
python3 -m harvest.src.core.wsl_harvester -d example.com -s "google,bing" -l 1000
python3 -m harvest.src.core.wsl_harvester -d example.com --export-windows
```

Batch:
```bash
echo "example.com" > targets.txt
echo "example.org" >> targets.txt
python3 -m harvest.src.core.batch_processor targets.txt
```

Outputs:
- Raw: `src/data/outputs/leads/raw_leads/DOMAIN_TIMESTAMP.txt`
- Reports/exports: under `src/data/outputs/leads/exports/` (CSV/JSON helpers)

Notes:
- Some integrations (Hunter, LinkedIn, email verification) are stubbed.
- theHarvester binary must be installed for real scans; tests mock subprocess.
- Designed for WSL; Windows export path is best-effort.
