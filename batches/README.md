# Batch config examples

YAML configs for the pipeline orchestrator. Run with:

```bash
python -m pipeline.orchestrator --config batches/<file>.yaml
```

## City sweep (collect → dedupe → verify → pack)

| File | Niche | City/State |
|------|--------|------------|
| `city_sweep_example.yaml` | med spas | Charlotte, NC |
| `city_sweep_fitness.yaml` | fitness studios, gyms | Austin, TX |
| `city_sweep_coffee.yaml` | coffee shops, roasters | Portland, OR |
| `city_sweep_auto_repair.yaml` | auto repair, mechanics | Denver, CO |
| `city_sweep_veterinarians.yaml` | vets, animal hospitals | Seattle, WA |
| `city_sweep_salons.yaml` | salons, barbershops | Nashville, TN |
| `city_sweep_home_services.yaml` | HVAC, plumbing | Phoenix, AZ |
| `city_sweep_brewery.yaml` | breweries, taprooms | Asheville, NC |
| `city_sweep_accounting.yaml` | accounting, bookkeeping | Charlotte, NC |
| `city_sweep_childcare.yaml` | childcare, preschools | Raleigh, NC |
| `city_sweep_wellness.yaml` | yoga, PT, chiropractic | Boulder, CO |
| `city_sweep_landscaping.yaml` | landscaping, lawn care | Atlanta, GA |
| `city_sweep_florists.yaml` | florists, flower shops | San Antonio, TX |

## Other batch types

- `verify_pass_example.yaml` — re-verify existing candidates (no new collection)
- `pack_assembly_example.yaml` — assemble packs from already-verified leads
- `signal_sweep_example.yaml` — mixed-source sweep (e.g. Places + future theHarvester)

## Fields

- **batch_type**: `city_sweep` | `signal_sweep` | `verify_pass` | `pack_assembly`
- **city** (required), **state**, **country** (default `US`)
- **niche**: label for the pack (e.g. `fitness`, `coffee`)
- **query**: Google Places text search query (e.g. `"gyms in Austin TX"`)
- **limit**: max candidates to collect (default 50)
- **enrichment_tier**: `basic` | `enriched`
- **sources**: list, e.g. `["google_places"]`
- **max_freshness_days**: quality gate threshold (default 90)
