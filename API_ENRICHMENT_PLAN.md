# Enrichment Audit (Apollo + Hunter)

- Generator entrypoint: `leadgen/generator.py` → `generate_pack`.
- Enrichment tier check: `enrichment_tier == "enriched"` branches into extra work.
- Current enrichment hook: `LeadEnricher` (Apollo/Hunter person/email focus).
- BuiltWith + ScrapingBee already wired in enriched path; basic tier untouched.
- Models: `leadgen/models.py::LeadResult` holds business/analysis plus enrichment fields (tech_stack, scrape_source, etc.).
- Export: `leadgen/export.py` writes fixed CSV headers; JSONL includes base fields and optional enrichment.
- Hunter integration: `leadgen/integrations/hunter_client.py` (domain search + verify), used inside `LeadEnricher`.
- Apollo integration: `leadgen/integrations/apollo_client.py` (person/org match) but no org-level bulk/job-posting usage yet.
- CLI/start-pack: set `enrichment_tier` to “basic” or “enriched”; generator handles downstream enrichment.
- Logging: minimal; enrichment failures soft-fail.
- Tests touching enrichment: `tests/test_generator_enriched_packs.py`, `tests/test_enriched_export.py`, `tests/test_enrichment.py`, `tests/test_rate_limiting.py`, `tests/test_generator_contact_fallbacks.py`.
- Gaps: org-level Apollo bulk enrich + job postings not called; Hunter domain/email finder results not surfaced in LeadResult/exports.
