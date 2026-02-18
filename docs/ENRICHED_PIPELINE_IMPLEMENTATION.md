# Enriched Pipeline Implementation Notes

This document describes where enrichment currently plugs into the lead generation flow, and how to integrate future BuiltWith and ScrapingBee enrichment without breaking the existing generator.

## Current Flow
- Entry: `leadgen/generator.py:generate_pack`
- Standard steps:
  1. `search_places` → `get_details` to populate `Business` objects.
  2. `fetch_html` → `extract_emails` → `apply_email_patterns` → `analyze_html`.
  3. Build `LeadResult` objects and export CSV/JSONL.
- Enrichment hook:
  - Inside `generate_pack`, only when `enrichment_tier == "enriched"`.
  - Instantiates `ApolloClient` and `HunterClient` (if available).
  - Uses `LeadEnricher.enrich_lead` to add enrichment data to each `LeadResult`.

## Models
- `LeadResult` (leadgen/models.py) currently contains:
  - `business: Business`
  - `analysis: WebsiteAnalysis`
  - `enrichment: Optional[Dict]` (holds Apollo/Hunter data)
- `Business` holds website/email/phone/etc. No tech stack field yet (to be added for BuiltWith).

## Where to insert BuiltWith
- Within `generate_pack`’s `if enrichment_tier == "enriched":` block.
- After creating `LeadEnricher`, pass a BuiltWith client (to be added) so `enrich_lead` can fetch `tech_stack` for each domain.
- Soft-fail: if BuiltWith errors or is missing a key, return `None` for tech stack and continue.

## Where to insert ScrapingBee (tiered scraping)
- In the page-fetching step inside `generate_pack`:
  - Keep current `fetch_html` as the first attempt.
  - Detect empty/JS-rendered/blocked HTML. If so, call ScrapingBee client to fetch rendered HTML.
  - Use whichever HTML is better for email extraction and analysis.
- Soft-fail: if ScrapingBee fails, keep original HTML (even if empty) and continue.

## Soft-Fail Expectations
- No enrichment call should raise unhandled exceptions.
- Basic/standard packs must never call BuiltWith or ScrapingBee.
- Enriched packs should log or store errors but continue generating leads and exporting files.
- CSV/JSONL schema for standard packs must remain unchanged; enriched data should only add optional fields (e.g., `tech_stack`) in enrichment payloads.

## Export Schema for Enriched Packs
- Basic packs: headers remain unchanged (15 columns): name, address, website, phone, email, needs_website, needs_redesign, needs_chatbot, needs_ai_integration, score, recommended_services, outreach_message, enriched_title, verified_email_status, apollo_company.
- Enriched packs: same base headers plus appended columns: tech_stack, enrichment_used, scrape_source, email_confidence. These only appear when enriched leads are present; basic packs never include them.
- JSONL enriched fields: adds `tech_stack`, `scrape_source`, `enrichment_used`, and optional `email_confidence` alongside existing fields; `enrichment` dict remains included when present.
- Backward compatibility: basic packs continue to emit the exact legacy schema; enriched-only fields are appended (CSV) or added as optional keys (JSONL) without altering base keys.
