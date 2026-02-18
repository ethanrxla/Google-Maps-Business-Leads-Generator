# Leads Swarm Pipeline: Architecture & Execution Plan

## Executive Summary

1. **Current state**: Single-stage monolith in `leadgen/generator.py` -- search, enrich, and export happen in one synchronous pass with no separation between raw candidates, verified leads, and sellable packs
2. **Critical bugs**: Email extractor captures image filenames (`fancybox_sprite@2x.png`) as emails; BuiltWith API errors stored as "enriched" tech_stack data; Apollo org fields 0% populated
3. **Target state**: Three-stage pipeline (Collect -> Verify/Dedupe -> Pack) backed by Supabase, with quality gates before any pack is marked sellable
4. **Swarm design**: Four agents (Collector, Deduper, Verifier, Pack Assembler) coordinated by a single orchestrator, driven by YAML batch configs
5. **Cost strategy**: Google Places free tier + HTML scraping for collection ($0); Hunter/Apollo only for high-score leads (~$22/mo at 2000 leads/month)
6. **Supabase migration**: Six tables (`batch_runs`, `candidates`, `verified_leads`, `packs`, `pack_entries`, `pipeline_events`) with RLS policies, replacing CSV files and SQLite
7. **Dedup approach**: Composite key (normalized domain + city) for exact match, `rapidfuzz` for fuzzy matching at 85% threshold
8. **Quality gates**: 8 checks including email coverage, validity, phone coverage, dedup, pack fill rate, and score distribution -- all must pass for `sellable = true`
9. **Day 1 focus**: Supabase project creation, schema migration, email validation fix
10. **v1 definition of done**: 500+ verified leads, 10+ sellable packs across 5+ niches, full pipeline runnable from a single CLI command

---

## 1. System Architecture

### Current State (Single-Stage Monolith)

`leadgen/generator.py:generate_pack()` runs everything synchronously: search -> details -> fetch -> analyze -> enrich -> export. No separation between collection, verification, and packaging. The enriched CSV shows real data quality problems: Wix Sentry tokens as emails, BuiltWith `"API Credits: 0"` errors stored as tech_stack, and image sprite filenames captured as contact addresses.

### Target Architecture (Three-Stage Pipeline)

```
                    +-----------------------+
                    |   ORCHESTRATOR        |
                    |   pipeline/           |
                    |   orchestrator.py     |
                    +-----------+-----------+
                                |
          +---------------------+---------------------+
          |                     |                     |
    STAGE 1: COLLECT      STAGE 2: VERIFY       STAGE 3: PACK
    +--------------+     +---------------+     +---------------+
    | Collector    |     | Deduper       |     | PackAssembler |
    | Agent        |     | Verifier      |     | Agent         |
    +--------------+     +---------------+     +---------------+
    | Google Places|     | Email format  |     | Quality gate  |
    | theHarvester |     | MX check      |     | Dedupe check  |
    | HTML scrape  |     | Hunter verify |     | Score+rank    |
    | SERP/manual  |     | Social lookup |     | CSV/JSONL     |
    +-+----+----+--+     | Apollo enrich |     | export        |
      |    |    |        | Confidence    |     +-------+-------+
      v    v    v        +-------+-------+             |
    [candidates]              |                  [packs] +
    Supabase table       [verified_leads]        [pack_entries]
                         Supabase table          Supabase tables
```

### New Directory Structure

```
leads/
  pipeline/                    # NEW -- pipeline orchestration
    __init__.py
    orchestrator.py            # Chains stages, reads batch configs
    collector.py               # Stage 1: collection from multiple sources
    deduper.py                 # Stage 2a: cross-source identity resolution
    verifier.py                # Stage 2b: verification + confidence scoring
    pack_assembler.py          # Stage 3: quality gates + pack export
    models.py                  # Candidate, VerifiedLead, Pack dataclasses
    email_validator.py         # Email format + blocklist + MX check
    quality_gates.py           # Pack quality gate checks
    rate_limiter.py            # Per-service rate limiting
    batch_config.py            # YAML batch definition loader
  db/                          # NEW -- Supabase data layer
    __init__.py
    supabase_client.py         # Supabase Python client wrapper
    repositories.py            # CRUD for candidates, verified, packs
    migrations/
      001_core_tables.sql      # Schema from Section 7
      migrate_csv_to_supabase.py  # One-time CSV import script
  batches/                     # NEW -- batch job definitions
    city_sweep_example.yaml
    signal_sweep_example.yaml
    verify_pass_example.yaml
  leadgen/                     # EXISTING -- minimal changes
    email_extract.py           # MODIFY: add validation filter
    ai_scoring.py              # MODIFY: add lead_quality_score
    export.py                  # MODIFY: add social handle columns
    (all other files unchanged)
  backend/
    server.py                  # MODIFY: add pipeline endpoints
```

### Key Files Modified (Existing)

| File | Change |
|------|--------|
| `leadgen/email_extract.py` | Add `is_invalid_email()` filter before returning matches |
| `leadgen/ai_scoring.py` | Add `lead_quality_score()` (data completeness metric) alongside existing `score_lead()` (needs metric) |
| `leadgen/export.py` | Add social handle columns, dual score columns to CSV/JSONL headers |
| `backend/server.py` | Add `POST /pipeline/batch`, `GET /pipeline/batch/{id}`, `GET /pipeline/stats` |
| `.env` | Add `SUPABASE_URL`, `SUPABASE_SERVICE_KEY` |

---

## 2. Canonical Data Model

### Stage 1: `candidates` (Raw Collected)

```python
@dataclass
class Candidate:
    id: str                          # UUID
    name: str                        # Business name as collected
    name_normalized: str             # Lowercase, stripped Inc/LLC/etc.
    address: Optional[str]
    city: Optional[str]
    city_normalized: Optional[str]   # Lowercase, alphanumeric only
    state: Optional[str]
    country: str                     # Default "US"
    lat: Optional[float]
    lng: Optional[float]
    phone_raw: Optional[str]
    email_raw: Optional[str]
    email_source: Optional[str]      # "html", "pattern", "hunter", "places", "harvest"
    website: Optional[str]
    source: str                      # "google_places", "theharvester", "manual", "serp"
    source_id: Optional[str]         # place_id, domain, etc.
    collection_batch_id: str
    collected_at: datetime
    raw_data: Optional[dict]         # Full API response JSON
    # Website analysis flags
    has_website: Optional[bool]
    needs_website: Optional[bool]
    needs_redesign: Optional[bool]
    needs_chatbot: Optional[bool]
    needs_ai_integration: Optional[bool]
    # Pipeline state
    status: str                      # "new" | "deduped" | "sent_to_verify" | "invalid" | "duplicate"
    dedupe_cluster_id: Optional[str]
    dedup_key: str                   # Computed composite key
```

### Stage 2: `verified_leads` (Verified with Confidence)

```python
@dataclass
class VerifiedLead:
    id: str
    candidate_ids: list[str]         # All merged candidate IDs
    dedupe_cluster_id: str
    # Business info (best-of-merge)
    name: str
    name_normalized: str
    address: Optional[str]
    city: Optional[str]
    state: Optional[str]
    country: str
    lat: Optional[float]
    lng: Optional[float]
    # Verified contact
    phone: Optional[str]
    phone_verified: bool
    email: Optional[str]
    email_verified: bool
    email_confidence: int            # 0-100
    email_source: Optional[str]
    website: Optional[str]
    website_alive: Optional[bool]
    website_last_checked: Optional[datetime]
    # Social handles
    linkedin_url: Optional[str]
    twitter_handle: Optional[str]
    discord_invite: Optional[str]
    telegram_handle: Optional[str]
    facebook_url: Optional[str]
    instagram_handle: Optional[str]
    social_source: Optional[str]
    # Enrichment
    org_name: Optional[str]
    org_industry: Optional[str]
    org_employee_count: Optional[int]
    org_annual_revenue: Optional[float]
    org_linkedin_url: Optional[str]
    org_is_hiring: Optional[bool]
    tech_stack: Optional[dict]
    # Dual scoring
    needs_score: int                 # 0-100: how much they need services
    lead_quality_score: int          # 0-100: data completeness + verification
    recommended_services: list[str]
    # Analysis flags
    has_website: bool
    needs_website: bool
    needs_redesign: bool
    needs_chatbot: bool
    needs_ai_integration: bool
    # Metadata
    verification_batch_id: str
    verified_at: datetime
    verification_sources: list[str]
    data_freshness_days: int
    provenance: dict                 # Full audit trail
```

### Stage 3: `packs` + `pack_entries` (Sellable Bundles)

```python
@dataclass
class Pack:
    id: str
    pack_id: str                     # Slug: "usa_fl_miami_dentists_50"
    niche: Optional[str]
    city: Optional[str]
    state: Optional[str]
    country: Optional[str]
    lead_count: int
    enrichment_tier: str             # "basic" | "enriched"
    # Quality metrics
    email_coverage_pct: float
    email_verified_pct: float
    phone_coverage_pct: float
    website_coverage_pct: float
    avg_needs_score: float
    avg_quality_score: float
    duplicate_count: int             # Must be 0 for sellable
    # Status
    sellable: bool
    quality_gate_failures: list[str]
    assembled_at: datetime
    csv_path: Optional[str]
    jsonl_path: Optional[str]
    expires_at: Optional[datetime]   # 180-day freshness expiry
```

---

## 3. Verification Framework

### Verification States per Field

| State | Meaning | Example |
|-------|---------|---------|
| **verified** | Confirmed by external source or format validation | Email "deliverable" via Hunter |
| **unverified** | Collected but not yet checked | Email from HTML, unchecked |
| **invalid** | Checked and failed | Image filename, bounced email |

### Email Verification Rules

**Immediate rejection (invalid):**
- Matches image file pattern: `\.(png|jpg|jpeg|gif|svg|ico|webp|bmp)$`
- Contains known non-email tokens: `sentry`, `wixpress`, `cloudflare`, `noreply@`, `example.com`, `test@`
- Fails RFC 5322 format check
- Domain has no MX record (free DNS check)

**High confidence (80-100):** Hunter returns "deliverable" with score >= 80
**Medium confidence (40-79):** Hunter returns "risky", or email from contact page
**Low confidence (1-39):** Pattern-generated, or HTML-extracted without verification
**Zero confidence:** Invalid per above rules

### Email Confidence Scoring

```python
def compute_email_confidence(email, source, hunter_result=None):
    if is_invalid_email(email):
        return 0
    base = {"places": 30, "html": 25, "contact_page": 40,
            "pattern": 15, "hunter_domain_search": 50, "harvest": 20}.get(source, 10)
    if hunter_result:
        result = hunter_result.get("data", {}).get("result", "")
        score = hunter_result.get("data", {}).get("score", 0)
        if result == "deliverable": return max(base, score)
        elif result == "risky": return max(base, int(score * 0.7))
        elif result == "undeliverable": return 0
    return base
```

### Social Handle Verification

| Channel | Verified | Unverified | Invalid |
|---------|----------|------------|---------|
| X/Twitter | Profile exists, matches business | Found in HTML/Apollo, unchecked | 404 or suspended |
| Discord | Invite resolves to active server | Found on website, untested | Expired invite |
| Telegram | Handle resolves to channel/group | Found on website | 404 |
| LinkedIn | URL returns 200, matches business | From Apollo/Hunter/HTML | 404 |

### Social Discovery (cheap-first)
1. HTML scrape of business website: regex for `twitter.com/`, `discord.gg/`, `t.me/`, `linkedin.com/company/` -- free
2. Hunter.io response: already returns `twitter_url`, `linkedin_url` -- no extra cost
3. Apollo.io org data: returns `linkedin_url` -- already collected
4. Dedicated check: only for leads with needs_score > 60

---

## 4. Dedupe Strategy

### Composite Key

```python
def compute_dedup_key(name, city, website):
    domain = extract_domain(website)  # Reuse leadgen.enrichment._extract_domain
    city_norm = re.sub(r'[^a-z0-9]', '', city.lower()) if city else ""
    if domain:
        return f"domain:{domain.lower()}:{city_norm}"
    name_norm = normalize_business_name(name)
    return f"name:{name_norm}:{city_norm}"

def normalize_business_name(name):
    name = name.lower().strip()
    for suffix in [" inc", " llc", " ltd", " corp", " co", " dba"]:
        name = name.removesuffix(suffix)
    return re.sub(r'\s+', ' ', re.sub(r'[^a-z0-9\s]', '', name)).strip()
```

### Matching Tiers
1. **Exact**: Same `dedup_key` -> same cluster (domain + city match)
2. **Fuzzy**: `rapidfuzz.fuzz.ratio(name_a, name_b) >= 85` AND same city -> candidate merge
3. **Cross-source**: theHarvester domain + Google Places `place_id` -> merge if domain matches

### Merge Strategy
- Keep record with most populated fields as primary
- Fill missing fields from secondary records
- For conflicting values (two emails): keep both, verifier picks highest-confidence
- Track all `candidate_ids` in `verified_leads.candidate_ids[]`

---

## 5. Swarm-Agent Design

### Agent 1: Collector (`pipeline/collector.py`)

| | Detail |
|---|---|
| **Input** | `CollectionJob`: query, source_type, city, state, country, niche, limit, batch_id |
| **Output** | Rows in `candidates` table; returns `CollectionResult` with count + errors |
| **Sources** | `google_places` -> `leadgen.places`, `theharvester` -> `harvest.src.core`, `html_scrape` -> `leadgen.website_fetch` + `email_extract`, `manual` -> direct insert |
| **Failure** | Per-source retry (3x exponential backoff). On total failure: mark batch `status="error"`, log, continue |
| **Handoff** | Sets candidate rows to `status="new"`, writes `collection_complete` event |

### Agent 2: Deduper (`pipeline/deduper.py`)

| | Detail |
|---|---|
| **Input** | `batch_id` (optional); reads `candidates WHERE status="new"` |
| **Output** | Updates `dedupe_cluster_id` and `status` on candidates |
| **Logic** | Compute dedup_key -> group -> assign cluster IDs -> fuzzy pass on singletons |
| **Failure** | Pure DB ops, retry 3x on transient errors. Idempotent. |
| **Handoff** | Sets status to `"deduped"` |

### Agent 3: Verifier (`pipeline/verifier.py`)

| | Detail |
|---|---|
| **Input** | Reads `candidates WHERE status="deduped"`; `VerificationConfig` with API budget |
| **Output** | Inserts into `verified_leads`; updates candidate status to `"sent_to_verify"` |
| **Steps** | 1) Email format + blocklist (free) 2) MX check (free) 3) Website alive (free) 4) Social extraction from HTML (free) 5) Hunter verify (paid, needs_score >= 40) 6) Apollo enrich (paid, needs_score >= 50) |
| **Cost gate** | Tracks API calls; stops paid calls when budget exceeded |
| **Failure** | Soft-fail per lead (existing pattern). Lead gets base confidence only. |
| **Handoff** | Writes to `verified_leads` with full provenance |

### Agent 4: Pack Assembler (`pipeline/pack_assembler.py`)

| | Detail |
|---|---|
| **Input** | `PackSpec`: niche, city, state, country, target_count, enrichment_tier, quality_floor |
| **Output** | Rows in `packs` + `pack_entries`; CSV/JSONL files; `PackResult` with metrics |
| **Logic** | Query verified leads -> sort by quality -> take top N -> run quality gates -> export |
| **Failure** | Idempotent; re-run overwrites old files |

### Orchestrator (`pipeline/orchestrator.py`)

```python
class PipelineOrchestrator:
    def run_batch(self, batch_config):
        """Full pipeline: collect -> dedupe -> verify -> assemble."""
    def run_verify_only(self, batch_id=None):
        """Re-verify existing candidates without re-collecting."""
    def run_pack_only(self, pack_spec):
        """Re-assemble a pack from existing verified data."""
```

---

## 6. Batch Strategy

### Type 1: City/Type Bulk Sweep
```yaml
batch_type: city_sweep
jobs:
  - source: google_places
    query: "dentists in Miami FL"
    city: Miami
    state: FL
    niche: dentists
    limit: 60
pack_specs:
  - niche: dentists
    state: FL
    target_count: 50
```
Run: `python -m pipeline.orchestrator --config batches/city_sweep.yaml`

### Type 2: Signal/Community Sweep
Mixed sources for niches where Places alone is insufficient: combine Places queries with theHarvester domain scans and manual entries.

### Type 3: Verification + Dedupe Pass
No new collection. Run verification and dedup on existing unverified candidates with configurable API budgets.

### Type 4: Pack Assembly Pass
Assemble packs from already-verified leads. Useful for re-cutting packs (different sizes, different quality floors) without re-collecting.

---

## 7. Supabase Target Schema

### Tables

```sql
-- Batch run tracking
CREATE TABLE batch_runs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    batch_type TEXT NOT NULL CHECK (batch_type IN ('city_sweep','signal_sweep','verify_pass','pack_assembly')),
    config JSONB NOT NULL DEFAULT '{}',
    status TEXT NOT NULL DEFAULT 'pending' CHECK (status IN ('pending','running','completed','error')),
    started_at TIMESTAMPTZ,
    completed_at TIMESTAMPTZ,
    error_message TEXT,
    stats JSONB DEFAULT '{}',
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- Stage 1: Raw candidates
CREATE TABLE candidates (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name TEXT NOT NULL,
    name_normalized TEXT NOT NULL,
    address TEXT,
    city TEXT,
    city_normalized TEXT,
    state TEXT,
    country TEXT DEFAULT 'US',
    lat DOUBLE PRECISION,
    lng DOUBLE PRECISION,
    phone_raw TEXT,
    email_raw TEXT,
    email_source TEXT,
    website TEXT,
    source TEXT NOT NULL,
    source_id TEXT,
    collection_batch_id UUID REFERENCES batch_runs(id),
    collected_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    raw_data JSONB,
    has_website BOOLEAN,
    needs_website BOOLEAN,
    needs_redesign BOOLEAN,
    needs_chatbot BOOLEAN,
    needs_ai_integration BOOLEAN,
    status TEXT NOT NULL DEFAULT 'new',
    dedupe_cluster_id UUID,
    dedup_key TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- Stage 2: Verified leads
CREATE TABLE verified_leads (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    candidate_ids UUID[] NOT NULL,
    dedupe_cluster_id UUID,
    name TEXT NOT NULL,
    name_normalized TEXT NOT NULL,
    address TEXT,
    city TEXT,
    state TEXT,
    country TEXT DEFAULT 'US',
    lat DOUBLE PRECISION,
    lng DOUBLE PRECISION,
    phone TEXT,
    phone_verified BOOLEAN DEFAULT FALSE,
    email TEXT,
    email_verified BOOLEAN DEFAULT FALSE,
    email_confidence INTEGER DEFAULT 0 CHECK (email_confidence BETWEEN 0 AND 100),
    email_source TEXT,
    website TEXT,
    website_alive BOOLEAN,
    website_last_checked TIMESTAMPTZ,
    linkedin_url TEXT,
    twitter_handle TEXT,
    discord_invite TEXT,
    telegram_handle TEXT,
    facebook_url TEXT,
    instagram_handle TEXT,
    social_source TEXT,
    org_name TEXT,
    org_industry TEXT,
    org_employee_count INTEGER,
    org_annual_revenue NUMERIC,
    org_linkedin_url TEXT,
    org_is_hiring BOOLEAN,
    tech_stack JSONB,
    needs_score INTEGER NOT NULL DEFAULT 0 CHECK (needs_score BETWEEN 0 AND 100),
    lead_quality_score INTEGER NOT NULL DEFAULT 0 CHECK (lead_quality_score BETWEEN 0 AND 100),
    recommended_services TEXT[],
    has_website BOOLEAN NOT NULL DEFAULT FALSE,
    needs_website BOOLEAN NOT NULL DEFAULT FALSE,
    needs_redesign BOOLEAN NOT NULL DEFAULT FALSE,
    needs_chatbot BOOLEAN NOT NULL DEFAULT FALSE,
    needs_ai_integration BOOLEAN NOT NULL DEFAULT FALSE,
    verification_batch_id UUID REFERENCES batch_runs(id),
    verified_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    verification_sources TEXT[],
    data_freshness_days INTEGER DEFAULT 0,
    provenance JSONB DEFAULT '{}',
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- Stage 3: Packs
CREATE TABLE packs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    pack_id TEXT UNIQUE NOT NULL,
    niche TEXT,
    city TEXT,
    state TEXT,
    country TEXT DEFAULT 'US',
    lead_count INTEGER NOT NULL DEFAULT 0,
    enrichment_tier TEXT NOT NULL DEFAULT 'basic',
    email_coverage_pct NUMERIC(5,2) DEFAULT 0,
    email_verified_pct NUMERIC(5,2) DEFAULT 0,
    phone_coverage_pct NUMERIC(5,2) DEFAULT 0,
    website_coverage_pct NUMERIC(5,2) DEFAULT 0,
    avg_needs_score NUMERIC(5,2) DEFAULT 0,
    avg_quality_score NUMERIC(5,2) DEFAULT 0,
    duplicate_count INTEGER DEFAULT 0,
    sellable BOOLEAN DEFAULT FALSE,
    quality_gate_failures TEXT[],
    assembled_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    assembly_batch_id UUID REFERENCES batch_runs(id),
    csv_path TEXT,
    jsonl_path TEXT,
    expires_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- Pack <-> verified_leads junction
CREATE TABLE pack_entries (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    pack_id TEXT NOT NULL REFERENCES packs(pack_id) ON DELETE CASCADE,
    verified_lead_id UUID NOT NULL REFERENCES verified_leads(id),
    position_in_pack INTEGER NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    UNIQUE(pack_id, verified_lead_id),
    UNIQUE(pack_id, position_in_pack)
);

-- Pipeline event log
CREATE TABLE pipeline_events (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    batch_id UUID REFERENCES batch_runs(id),
    event_type TEXT NOT NULL,
    payload JSONB DEFAULT '{}',
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
```

### Indexes
```sql
CREATE INDEX idx_candidates_status ON candidates(status);
CREATE INDEX idx_candidates_dedup_key ON candidates(dedup_key);
CREATE INDEX idx_candidates_batch ON candidates(collection_batch_id);
CREATE INDEX idx_candidates_city ON candidates(city_normalized, source);
CREATE INDEX idx_candidates_cluster ON candidates(dedupe_cluster_id) WHERE dedupe_cluster_id IS NOT NULL;
CREATE INDEX idx_verified_city_score ON verified_leads(city, needs_score DESC);
CREATE INDEX idx_verified_quality ON verified_leads(lead_quality_score DESC);
CREATE INDEX idx_verified_batch ON verified_leads(verification_batch_id);
CREATE INDEX idx_packs_sellable ON packs(sellable) WHERE sellable = TRUE;
CREATE INDEX idx_pack_entries_pack ON pack_entries(pack_id);
CREATE INDEX idx_pack_entries_lead ON pack_entries(verified_lead_id);
```

### RLS Policies
```sql
ALTER TABLE candidates ENABLE ROW LEVEL SECURITY;
ALTER TABLE verified_leads ENABLE ROW LEVEL SECURITY;
ALTER TABLE packs ENABLE ROW LEVEL SECURITY;
ALTER TABLE pack_entries ENABLE ROW LEVEL SECURITY;

-- Service role (backend) full access
CREATE POLICY "service_full" ON candidates FOR ALL USING (auth.role() = 'service_role');
CREATE POLICY "service_full" ON verified_leads FOR ALL USING (auth.role() = 'service_role');
CREATE POLICY "service_full" ON packs FOR ALL USING (auth.role() = 'service_role');
CREATE POLICY "service_full" ON pack_entries FOR ALL USING (auth.role() = 'service_role');

-- Anon can only view sellable packs (storefront)
CREATE POLICY "anon_sellable_packs" ON packs FOR SELECT USING (sellable = TRUE);
```

### Migration from CSV
1. Create Supabase project, get credentials, add to `.env`
2. Run schema SQL via Supabase SQL Editor
3. Script (`db/migrations/migrate_csv_to_supabase.py`): read each CSV from `data/packs/*.csv`, parse with existing `CSV_HEADERS`, insert into `candidates` with `source="google_places"`, `status="new"`
4. Run deduper + verifier (format-only, no paid APIs) on imported data
5. Keep original CSV files as backup

---

## 8. Quality Gates

A pack must pass ALL gates to be `sellable = true`:

| Gate | Basic Pack | Enriched Pack |
|------|-----------|---------------|
| Email coverage | >= 70% have email | >= 85% have email |
| Email validity | 0 invalid emails | 0 invalid emails |
| Email verified | n/a | >= 30% Hunter-verified |
| Phone coverage | >= 75% have phone | >= 85% have phone |
| Website coverage | >= 60% have website | >= 60% have website |
| Deduplication | 0 duplicates in pack | 0 duplicates in pack |
| Pack fill rate | >= 80% of target count | >= 80% of target count |
| Data freshness | Collected/verified within 90 days | Collected/verified within 90 days |
| Score distribution | avg needs_score >= 15, >= 20% have score >= 30 | Same |

Implementation: `pipeline/quality_gates.py:check_quality_gates(pack, leads) -> (bool, list[str])`

---

## 9. Cost/Performance Strategy

### Collection (Cheap-First)

| Priority | Source | Cost | Status |
|----------|--------|------|--------|
| 1 | Google Places Text Search | $0 (free tier ~10K/mo) | Existing |
| 2 | Google Place Details | $0 (included in free tier) | Existing |
| 3 | HTML fetch + email extract | $0 (self-hosted) | Existing, needs fix |
| 4 | Pattern email generation | $0 (computation) | Existing |
| 5 | theHarvester OSINT | $0 (free sources) | Existing |
| 6 | DNS MX record check | $0 (standard DNS) | New |

### Verification (Selective Paid)

| Source | ~Cost/call | When | Expected % of leads |
|--------|-----------|------|---------------------|
| Hunter Email Verify | $0.02 | needs_score >= 40 | ~30% |
| Hunter Domain Search | $0.02 | No email + needs_score >= 50 | ~15% |
| Apollo Org Enrich | $0.02 | Enriched tier only | ~20% |
| ScrapingBee | $0.002 | JS-rendered sites failing basic fetch | ~5% |

### Monthly Estimate at 2000 leads/month: ~$22

### Performance Optimizations
1. **Cache Hunter results** in `provenance` JSON -- skip re-verify if < 30 days old
2. **Bulk Apollo org enrich** -- already implemented, batches of 50
3. **Async HTML fetch** -- add `asyncio` + `aiohttp` for parallel collection (10 concurrent)
4. **Daily collection caps** -- max 500 Places searches/day to stay in free tier

---

## 10. Security/Compliance

### Scraping Boundaries

| Platform | Allowed | Not Allowed |
|----------|---------|-------------|
| Google Places | Official API | Scraping Maps HTML |
| Business websites | Public pages, respect robots.txt | Mass crawling beyond reasonable rate |
| LinkedIn | Data from Apollo/Hunter APIs | Direct scraping |
| X/Twitter | Extract handle from HTML | Automated following/DMs |
| Discord | Extract invite links from HTML | Joining servers to scrape members |

### Rate Limiting
`pipeline/rate_limiter.py`: Per-service configurable limits
- Google Places: 10 req/sec
- Hunter: 10 req/min
- Apollo: 5 req/min
- HTML fetch: 20 req/sec
- theHarvester: 1 job at a time

### Data Provenance
Every `verified_leads` record tracks full provenance in JSONB:
```json
{
  "collection": {"source": "google_places", "place_id": "ChIJ...", "collected_at": "..."},
  "email": {"raw_source": "html", "hunter_verify": {"result": "deliverable", "score": 94}},
  "social": {"linkedin_url": {"source": "apollo"}, "twitter_handle": {"source": "html_scrape"}}
}
```

### Compliance
- B2B data from public directories -- GDPR applies narrowly but provenance is tracked
- Add `DELETE /api/lead/{email}` endpoint for right-to-deletion requests
- Pack documentation must note CAN-SPAM requirements for buyers
- `packs.expires_at` = 180 days; stale packs marked `sellable = false`

---

## 11. 14-Day Execution Roadmap

### Days 1-3: Foundation

**Day 1: Supabase + Schema**
- Create Supabase project, add `SUPABASE_URL` + `SUPABASE_SERVICE_KEY` to `.env`
- Run schema SQL (Section 7) via SQL Editor
- Create `db/supabase_client.py` + `db/repositories.py` with basic CRUD
- Test: insert one candidate, read it back
- Acceptance: all 6 tables exist, CRUD works

**Day 2: Email Validation Fix + Validator Module**
- Add `is_invalid_email()` to `leadgen/email_extract.py`: reject image patterns, sentry tokens, example.com
- Create `pipeline/email_validator.py` with full validation + MX check
- Fix BuiltWith: if API returns error JSON, set `tech_stack = None`
- Write tests for email validation against known bad examples
- Acceptance: `fancybox_sprite@2x.png` rejected, `info@dentist.com` accepted

**Day 3: CSV Migration + Pipeline Models**
- Create `db/migrations/migrate_csv_to_supabase.py`
- Import all 13+ existing CSV packs into `candidates` table
- Create `pipeline/models.py` with Candidate, VerifiedLead, Pack dataclasses
- Acceptance: all existing leads appear in Supabase `candidates` table

### Days 4-7: Pipeline Agents

**Day 4: Collector Agent**
- Create `pipeline/collector.py` wrapping existing Places + fetch + analyze + extract
- Output writes to `candidates` via `db/repositories.py`
- Acceptance: `python -m pipeline.collector --query "dentists in Boca Raton" --limit 20` inserts 20 candidates

**Day 5: Deduper Agent**
- Create `pipeline/deduper.py` with `compute_dedup_key()` + fuzzy matching
- Add `rapidfuzz` dependency
- Run on migrated data, report duplicate count
- Acceptance: two candidates with same domain+city get same cluster ID

**Day 6: Verifier Agent (Free)**
- Create `pipeline/verifier.py` with free checks: email format, MX, website alive, social extraction
- Implement confidence scoring formula
- Acceptance: verify 20 leads, all get confidence scores, social handles extracted where present

**Day 7: Verifier Agent (Paid) + Rate Limiter**
- Add Hunter verify + Apollo enrich to verifier (budget-gated)
- Create `pipeline/rate_limiter.py`
- Acceptance: verify 10 leads with Hunter, email_confidence updates

### Days 8-10: Assembly + Scoring + Orchestration

**Day 8: Pack Assembler + Quality Gates**
- Create `pipeline/pack_assembler.py` + `pipeline/quality_gates.py`
- Query verified leads, apply gates, export CSV/JSONL
- Acceptance: assemble one pack, quality gate report generated

**Day 9: Scoring Overhaul**
- Add `lead_quality_score()` to `leadgen/ai_scoring.py`:
  - +20 email present, +15 email_confidence >= 50, +10 phone, +10 website alive
  - +10 any social handle, +10 org_industry, +5 org_employee_count
  - +10 complete address, +10 needs_score >= 30
- Update `leadgen/export.py` with social columns + dual scores
- Acceptance: leads have both needs_score and lead_quality_score

**Day 10: Orchestrator + Batch Configs**
- Create `pipeline/orchestrator.py` chaining all agents
- Create `pipeline/batch_config.py` + example YAML configs in `batches/`
- CLI: `python -m pipeline.orchestrator --config batches/city_sweep.yaml`
- Acceptance: full pipeline runs end-to-end from single command

### Days 11-13: Integration + Production

**Day 11: Backend Endpoints**
- Add `POST /pipeline/batch`, `GET /pipeline/batch/{id}`, `GET /pipeline/stats` to `backend/server.py`
- Update `/admin/packs` to read from Supabase
- Acceptance: batch can be triggered via API

**Day 12: Bulk Collection Run**
- Define 10 city/niche combos, run through pipeline
- Target: 500+ candidates, 300+ verified, 5+ sellable packs
- Fix issues found during bulk run
- Acceptance: 5+ packs with `sellable = true`

**Day 13: Production Hardening**
- Error handling audit across all pipeline stages
- Logging standardization
- Environment variable validation on startup
- Acceptance: pipeline recovers from API failures without crashing

### Day 14: Testing + Documentation + Launch

- Run full test suite, write integration test (`tests/test_pipeline_e2e.py`)
- Update `AGENTS.md` with new pipeline module descriptions
- Final quality review: 10+ sellable packs across 5+ niches
- Acceptance: all tests pass, documentation current, packs sellable

---

## 12. Risk Register

| # | Risk | Likelihood | Impact | Mitigation |
|---|------|-----------|--------|------------|
| R1 | Google Places free tier exhausted | Medium | High | Daily caps (500 searches/day), monitor usage, fallback to theHarvester |
| R2 | Hunter/Apollo rate-limited or suspended | Medium | Medium | Rate limiter, budget caps, graceful degradation to base confidence |
| R3 | Email validation false positives | Low | Medium | Conservative blocklist, test against known-good emails before deploy |
| R4 | CSV migration data loss | Low | High | Keep original CSVs untouched, dry-run migration first, backup data/packs/ |
| R5 | Dedup false positives (different businesses merged) | Medium | Medium | Require domain match OR fuzzy >= 85 AND same city; log all merges in provenance |
| R6 | Dedup false negatives (duplicates not caught) | Medium | Low | Iterative threshold tuning, not a v1 blocker |
| R7 | BuiltWith API quota never recovers | High | Low | Already exhausted. Remove from critical path, use HTML-based tech detection |
| R8 | Supabase free tier limits (50K rows) | Medium | Medium | At 2K/month, takes ~2 years. Prune invalid/duplicate candidates older than 6 months. Upgrade to Pro ($25/mo) if needed. |
| R9 | Single operator bottleneck | High | High | Automate batch scheduling, self-describing YAML configs, document all processes |
| R10 | Pack quality insufficient for buyers | Medium | High | Quality gates are primary defense. Pilot with 5 packs to friendly buyers. Satisfaction guarantee with 7-day lead replacement. |

---

## A) Day 1 Exact Tasks

1. **Create Supabase project** at supabase.com (free tier)
2. **Copy project URL and service role key** into `.env`:
   ```
   SUPABASE_URL=https://xxxxx.supabase.co
   SUPABASE_SERVICE_KEY=eyJ...
   ```
3. **Run the schema SQL** from Section 7 in Supabase SQL Editor (all 6 tables + indexes + RLS + triggers)
4. **Install `supabase` Python package**: `pip install supabase`
5. **Create `db/` directory** with `__init__.py`, `supabase_client.py`, `repositories.py`
6. **Implement `supabase_client.py`**: single `get_client()` function returning configured Supabase client
7. **Implement `repositories.py`**: `insert_candidate()`, `get_candidates(filters)`, `update_candidate()` -- minimum CRUD
8. **Smoke test**: write a script that inserts one candidate row and reads it back
9. **Create `pipeline/` directory** with `__init__.py` -- just the package stub
10. **Verify** in Supabase dashboard: table exists, row visible, RLS policies active

## B) Definition of Done for v1 Shipment

All of these must be true:

- [ ] Supabase schema deployed with all 6 tables, indexes, and RLS policies
- [ ] Email extraction bug fixed: no image filenames, sentry tokens, or example.com emails in output
- [ ] Pipeline runs end-to-end: `python -m pipeline.orchestrator --config batches/X.yaml` completes without error
- [ ] 500+ candidates in `candidates` table across 5+ niches
- [ ] 300+ verified leads in `verified_leads` table with email_confidence scores
- [ ] 10+ packs in `packs` table with `sellable = true`
- [ ] Every sellable pack passes all 8 quality gates
- [ ] Zero duplicate leads within any single pack
- [ ] Dual scoring operational: every verified lead has both `needs_score` and `lead_quality_score`
- [ ] Backend endpoints functional: `/pipeline/batch`, `/pipeline/batch/{id}`, `/pipeline/stats`
- [ ] Full provenance JSON tracked for every verified lead
- [ ] Rate limiting active for all paid APIs
- [ ] All existing CSV pack data migrated into Supabase
- [ ] `pytest` passes with no failures
- [ ] Integration test covers full pipeline (collect -> dedupe -> verify -> pack)
