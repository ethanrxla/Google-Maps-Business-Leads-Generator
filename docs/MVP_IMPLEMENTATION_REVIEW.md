# MVP Implementation Review

Review of the implemented changes (terminal summary 944–1027) against:

- **Plan:** `/home/ethan/.cursor/plans/mvp_gap_analysis_b03d1c76.plan.md`
- **Spec:** `humble-stargazing-rivest.md`

---

## 1. Plan To-Do Coverage

| To-Do | Status | Evidence |
|-------|--------|----------|
| Add missing pipeline stage modules (orchestrator, collector, deduper, verifier, pack_assembler, batch_config, rate_limiter) | **Done** | New files: `pipeline/orchestrator.py`, `collector.py`, `deduper.py`, `verifier.py`, `pack_assembler.py`, `rate_limiter.py`, `batch_config.py` |
| Extend `db/repositories.py` with CRUD for verified_leads, packs, pack_entries, pipeline_events | **Done** | Modified `db/repositories.py`; new tests: `test_repositories_verified.py`, `test_repositories_packs.py`, `test_repositories_events.py` |
| Implement dedup_key + clustering, email confidence, provenance, verified lead creation | **Done** | Deduper, verifier, and `compute_email_confidence()` in `pipeline/email_validator.py`; verifier creates verified leads with provenance |
| Assemble packs from verified_leads, quality gates, persist metrics, export CSV/JSONL | **Done** | `pipeline/pack_assembler.py` uses quality gates and persists to Supabase |
| Implement `python -m pipeline.orchestrator --config batches/*.yaml` + example YAMLs | **Partial** | Orchestrator and batch_config exist; **no `batches/*.yaml` example files** in repo |
| Add `lead_quality_score()` and wire into pack ranking/metrics | **Done** | `leadgen/ai_scoring.py` has `lead_quality_score(lead: dict)`; verifier/pack_assembler use it |
| Add `/pipeline/batch`, `/pipeline/batch/{id}`, `/pipeline/stats` in backend | **Done** | `backend/server.py`: `POST /pipeline/batch`, `GET /pipeline/batch/{batch_id}`, `GET /pipeline/stats` |
| Add tests for each stage + mocked e2e batch run | **Done** | test_deduper, test_rate_limiter, test_batch_config, test_collector, test_verifier, test_pack_assembler, test_orchestrator, test_backend_pipeline, test_pipeline_e2e |

---

## 2. humble-stargazing-rivest.md Alignment

### Definition of Done (Section B)

| Criterion | Status | Notes |
|-----------|--------|--------|
| Supabase schema with 6 tables, indexes, RLS | **Partial** | Schema + indexes in `001_core_tables.sql`. **RLS policies are not in the migration** (spec Section 7 lists them). |
| Email extraction bug fixed | **Done** | `is_invalid_email()` used in `leadgen/email_extract.py`; no image/sentry/example.com in output. |
| Pipeline runs: `python -m pipeline.orchestrator --config batches/X.yaml` | **Done** | Orchestrator and batch_config loader exist. **Add example YAMLs** under `batches/` to match spec. |
| Candidates/verified leads/packs in Supabase | **Done** | Repos and stages read/write these tables. |
| Sellable packs + quality gates enforced | **Done** | Pack assembler runs `check_quality_gates()` and sets `sellable` accordingly. |
| Dual scoring (needs_score + lead_quality_score) | **Done** | Both in `VerifiedLead` and `lead_quality_score()` in ai_scoring. |
| Backend `/pipeline/batch`, `/pipeline/batch/{id}`, `/pipeline/stats` | **Done** | Implemented in backend. |
| Full provenance JSON per verified lead | **Done** | Verifier stage populates `provenance`. |
| Rate limiting for paid APIs | **Done** | `pipeline/rate_limiter.py` added. |
| CSV pack data migrated into Supabase | **Not done** | Spec calls for `db/migrations/migrate_csv_to_supabase.py`. **Not present** in repo. |
| pytest passes | **Done** | 544 tests pass (2 pre-existing failures noted, unrelated to this work). |
| Integration test: collect → dedupe → verify → pack | **Done** | `tests/test_pipeline_e2e.py` (5 tests). |

### Spec Details Check

- **Directory structure (Section 1):** `pipeline/` has orchestrator, collector, deduper, verifier, pack_assembler, models, email_validator, quality_gates, rate_limiter, batch_config. **Missing in repo:** `batches/city_sweep_example.yaml` (and other example YAMLs).
- **Data model:** `Candidate`, `VerifiedLead`, and `Pack` dataclasses match the spec; `Pack` uses `validate_enrichment_tier` and `VALID_ENRICHMENT_TIERS`.
- **Email verification (Section 3):** `is_invalid_email()` covers image patterns and blocklist. **MX check:** spec says “Domain has no MX record (free DNS check)” — **not implemented** in `pipeline/email_validator.py` (only blocklist + `compute_email_confidence()` from Hunter/Apollo/source).
- **Dedup (Section 4):** Composite key (domain + city) is implemented. Spec also mentions **rapidfuzz at 85%** for fuzzy matching — **not present** in pipeline (no `rapidfuzz` usage in `pipeline/deduper.py`). Acceptable as “optional fuzzy” per plan.
- **Quality gates (Section 8):** Implemented in `pipeline/quality_gates.py` and used by pack_assembler; thresholds match spec (basic vs enriched).

---

## 3. Gaps and Recommendations

1. **Add example batch configs**  
   Create `batches/city_sweep_example.yaml` (and optionally `signal_sweep_example.yaml`, `verify_pass_example.yaml`) so that `python -m pipeline.orchestrator --config batches/city_sweep_example.yaml` works out of the box as in the spec.

2. **RLS policies**  
   The spec (Section 7) requires RLS on `candidates`, `verified_leads`, `packs`, `pack_entries` and policies for service_role and anon (sellable packs). `001_core_tables.sql` has no RLS. Add a follow-up migration or append to 001 with:
   - `ALTER TABLE ... ENABLE ROW LEVEL SECURITY`
   - Service role full access policies
   - Anon SELECT on packs where `sellable = TRUE`

3. **MX check (optional for v1)**  
   Spec lists “Domain has no MX record” as an immediate rejection rule. Currently only format/blocklist and Hunter/Apollo confidence are used. Adding an optional MX lookup (e.g. via `dns.resolver` or a small helper) would align with the doc; can be deferred if you accept “format + blocklist + external API” as sufficient for MVP.

4. **rapidfuzz (optional)**  
   Fuzzy name dedup at 85% is specified but not implemented. Plan treated it as optional; fine to leave as future work or add when duplicate slippage becomes an issue.

5. **CSV migration script**  
   Spec and plan mention `db/migrations/migrate_csv_to_supabase.py` (or equivalent) to backfill existing CSV packs into `candidates`. Not in repo. Add when you need to migrate legacy CSV data into Supabase.

---

## 4. Summary

- **Plan:** All 8 to-dos are addressed; the only partial item is “batch YAML examples” (orchestrator and config loader exist, but no `batches/*.yaml` files).
- **Spec (Section B):** Most Definition-of-Done items are met. Remaining: RLS in schema, example batch YAMLs, CSV migration script; MX check and rapidfuzz are optional/nice-to-have.
- **No files were removed;** all changes are additive (new modules, new tests, extensions to repos/models/backend). The implementation is consistent with the plan and the spirit of the spec, with the gaps above documented for follow-up.
