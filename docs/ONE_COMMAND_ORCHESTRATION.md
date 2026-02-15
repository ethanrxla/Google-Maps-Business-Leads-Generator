# One-command orchestration (collect -> verify/dedupe -> pack)

Entrypoints:
- `./run_orchestration.sh` (recommended one-command wrapper)
- `leadgen/orchestrate_full_run.py` (direct module)

## What it does

`run_orchestration.sh` enforces execution safety:
- always runs with `/home/ethan/projects/Thei_Molt/leads/.venv/bin/python`
- performs dependency check first and only installs missing deps via venv pip (exact requirement spec per missing package)
- bounds each dependency install to 300s and applies a conservative orchestration wall timeout (`ORCH_WALL_TIMEOUT`, default `1800` seconds)


For each selected manifest target, in order:
1. **collect** via Google Places (`search_places`)
2. **verify/dedupe** with deterministic in-memory keying
3. **pack** via `generate_pack`

Artifacts are written under:
- `tmp_runs/orchestrated/<run_id>/collect/*.csv`
- `tmp_runs/orchestrated/<run_id>/verify_dedupe/*.csv`
- `tmp_runs/orchestrated/<run_id>/summary.json`

## Manifest format (YAML or JSON)

```yaml
targets:
  - id: miami_dentists
    query: "dentists in miami fl"
    country: USA
    state: Florida
    city: Miami
    niche: dentists
    limit: 25
    shard: A        # optional; if omitted, shard auto-assigned by stable hash
    enabled: true   # optional (default true)
```

## Usage

```bash
./run_orchestration.sh \
  --manifest docs/lead_pipeline_manifest.example.yaml \
  --shard A \
  --max-targets 10 \
  --timeout-seconds 900
```

## Conservative resource defaults

- sequential target execution (no fan-out workers)
- `--max-targets 10` default
- bounded per-target total runtime via `--timeout-seconds` (default `900`)

## Smoke command (safe)

```bash
./run_orchestration.sh \
  --manifest docs/lead_pipeline_manifest.example.yaml \
  --shard A \
  --dry-run \
  --max-targets 2 \
  --timeout-seconds 120
```

`summary.json` includes shard-scoped manifest selection metadata:
- `shard`
- `selected_count`
- `selected_target_ids`
