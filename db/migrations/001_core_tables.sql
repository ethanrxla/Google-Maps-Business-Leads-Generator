-- Migration 001: Core pipeline tables for the leads swarm pipeline.
--
-- Tables: batch_runs, candidates, verified_leads, packs, pack_entries, pipeline_events
-- Run this in the Supabase SQL Editor (or via psql) to set up the schema.
-- This migration is idempotent: uses IF NOT EXISTS where possible.

-- ============================================================================
-- BATCH RUNS - tracks every pipeline execution
-- ============================================================================
CREATE TABLE IF NOT EXISTS batch_runs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    batch_type TEXT NOT NULL CHECK (batch_type IN (
        'city_sweep', 'signal_sweep', 'verify_pass', 'pack_assembly'
    )),
    config JSONB NOT NULL DEFAULT '{}',
    status TEXT NOT NULL DEFAULT 'pending' CHECK (status IN (
        'pending', 'running', 'completed', 'error'
    )),
    started_at TIMESTAMPTZ,
    completed_at TIMESTAMPTZ,
    error_message TEXT,
    stats JSONB DEFAULT '{}',
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- ============================================================================
-- CANDIDATES - Stage 1: raw collected leads (unverified)
-- ============================================================================
CREATE TABLE IF NOT EXISTS candidates (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),

    -- Business identity
    name TEXT NOT NULL,
    name_normalized TEXT NOT NULL,

    -- Location
    address TEXT,
    city TEXT,
    city_normalized TEXT,
    state TEXT,
    country TEXT DEFAULT 'US',
    lat DOUBLE PRECISION,
    lng DOUBLE PRECISION,

    -- Contact (raw, unverified)
    phone_raw TEXT,
    email_raw TEXT,
    email_source TEXT,
    website TEXT,

    -- Collection metadata
    source TEXT NOT NULL CHECK (source IN (
        'google_places', 'theharvester', 'manual', 'serp', 'html_scrape'
    )),
    source_id TEXT,
    collection_batch_id UUID REFERENCES batch_runs(id),
    collected_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    raw_data JSONB,

    -- Website analysis (from HTML scrape)
    has_website BOOLEAN,
    needs_website BOOLEAN,
    needs_redesign BOOLEAN,
    needs_chatbot BOOLEAN,
    needs_ai_integration BOOLEAN,

    -- Pipeline state
    status TEXT NOT NULL DEFAULT 'new' CHECK (status IN (
        'new', 'deduped', 'sent_to_verify', 'invalid', 'duplicate'
    )),
    dedupe_cluster_id UUID,
    dedup_key TEXT,

    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- ============================================================================
-- VERIFIED LEADS - Stage 2: verified with confidence scores
-- ============================================================================
CREATE TABLE IF NOT EXISTS verified_leads (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),

    -- Links back to source candidates
    candidate_ids UUID[] NOT NULL,
    dedupe_cluster_id UUID,

    -- Business identity (best-of-merge)
    name TEXT NOT NULL,
    name_normalized TEXT NOT NULL,

    -- Location
    address TEXT,
    city TEXT,
    state TEXT,
    country TEXT DEFAULT 'US',
    lat DOUBLE PRECISION,
    lng DOUBLE PRECISION,

    -- Verified contact
    phone TEXT,
    phone_verified BOOLEAN DEFAULT FALSE,
    email TEXT,
    email_verified BOOLEAN DEFAULT FALSE,
    email_confidence INTEGER DEFAULT 0 CHECK (email_confidence >= 0 AND email_confidence <= 100),
    email_source TEXT,
    website TEXT,
    website_alive BOOLEAN,
    website_last_checked TIMESTAMPTZ,

    -- Social handles
    linkedin_url TEXT,
    twitter_handle TEXT,
    discord_invite TEXT,
    telegram_handle TEXT,
    facebook_url TEXT,
    instagram_handle TEXT,
    social_source TEXT,

    -- Enrichment data
    org_name TEXT,
    org_industry TEXT,
    org_employee_count INTEGER,
    org_annual_revenue NUMERIC,
    org_linkedin_url TEXT,
    org_is_hiring BOOLEAN,
    tech_stack JSONB,

    -- Scoring (dual)
    needs_score INTEGER NOT NULL DEFAULT 0 CHECK (needs_score >= 0 AND needs_score <= 100),
    lead_quality_score INTEGER NOT NULL DEFAULT 0 CHECK (lead_quality_score >= 0 AND lead_quality_score <= 100),
    recommended_services TEXT[],

    -- Analysis flags
    has_website BOOLEAN NOT NULL DEFAULT FALSE,
    needs_website BOOLEAN NOT NULL DEFAULT FALSE,
    needs_redesign BOOLEAN NOT NULL DEFAULT FALSE,
    needs_chatbot BOOLEAN NOT NULL DEFAULT FALSE,
    needs_ai_integration BOOLEAN NOT NULL DEFAULT FALSE,

    -- Verification metadata
    verification_batch_id UUID REFERENCES batch_runs(id),
    verified_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    verification_sources TEXT[],
    data_freshness_days INTEGER DEFAULT 0,
    provenance JSONB DEFAULT '{}',

    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- ============================================================================
-- PACKS - Stage 3: assembled sellable bundles
-- ============================================================================
CREATE TABLE IF NOT EXISTS packs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    pack_id TEXT UNIQUE NOT NULL,

    -- Pack definition
    niche TEXT,
    city TEXT,
    state TEXT,
    country TEXT DEFAULT 'US',
    lead_count INTEGER NOT NULL DEFAULT 0,
    enrichment_tier TEXT NOT NULL DEFAULT 'basic' CHECK (enrichment_tier IN ('basic', 'enriched')),

    -- Quality metrics (computed at assembly)
    email_coverage_pct NUMERIC(5,2) DEFAULT 0,
    email_verified_pct NUMERIC(5,2) DEFAULT 0,
    phone_coverage_pct NUMERIC(5,2) DEFAULT 0,
    website_coverage_pct NUMERIC(5,2) DEFAULT 0,
    avg_needs_score NUMERIC(5,2) DEFAULT 0,
    avg_quality_score NUMERIC(5,2) DEFAULT 0,
    duplicate_count INTEGER DEFAULT 0,

    -- Sellability
    sellable BOOLEAN DEFAULT FALSE,
    quality_gate_failures TEXT[],

    -- Assembly metadata
    assembled_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    assembly_batch_id UUID REFERENCES batch_runs(id),
    csv_path TEXT,
    jsonl_path TEXT,
    expires_at TIMESTAMPTZ,

    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- ============================================================================
-- PACK ENTRIES - junction: which verified leads belong to which pack
-- ============================================================================
CREATE TABLE IF NOT EXISTS pack_entries (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    pack_id TEXT NOT NULL REFERENCES packs(pack_id) ON DELETE CASCADE,
    verified_lead_id UUID NOT NULL REFERENCES verified_leads(id),
    position_in_pack INTEGER NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    UNIQUE(pack_id, verified_lead_id),
    UNIQUE(pack_id, position_in_pack)
);

-- ============================================================================
-- PIPELINE EVENTS - lightweight event log for stage transitions
-- ============================================================================
CREATE TABLE IF NOT EXISTS pipeline_events (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    batch_id UUID REFERENCES batch_runs(id),
    event_type TEXT NOT NULL,
    payload JSONB DEFAULT '{}',
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- ============================================================================
-- INDEXES
-- ============================================================================
CREATE INDEX IF NOT EXISTS idx_candidates_status ON candidates(status);
CREATE INDEX IF NOT EXISTS idx_candidates_dedup_key ON candidates(dedup_key);
CREATE INDEX IF NOT EXISTS idx_candidates_batch ON candidates(collection_batch_id);
CREATE INDEX IF NOT EXISTS idx_candidates_city ON candidates(city_normalized, source);
CREATE INDEX IF NOT EXISTS idx_candidates_cluster ON candidates(dedupe_cluster_id)
    WHERE dedupe_cluster_id IS NOT NULL;

CREATE INDEX IF NOT EXISTS idx_verified_city_score ON verified_leads(city, needs_score DESC);
CREATE INDEX IF NOT EXISTS idx_verified_quality ON verified_leads(lead_quality_score DESC);
CREATE INDEX IF NOT EXISTS idx_verified_batch ON verified_leads(verification_batch_id);

CREATE INDEX IF NOT EXISTS idx_packs_sellable ON packs(sellable) WHERE sellable = TRUE;
CREATE INDEX IF NOT EXISTS idx_pack_entries_pack ON pack_entries(pack_id);
CREATE INDEX IF NOT EXISTS idx_pack_entries_lead ON pack_entries(verified_lead_id);

CREATE INDEX IF NOT EXISTS idx_pipeline_events_batch ON pipeline_events(batch_id);
CREATE INDEX IF NOT EXISTS idx_pipeline_events_type ON pipeline_events(event_type);

-- ============================================================================
-- UPDATED_AT TRIGGER
-- ============================================================================
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Drop-if-exists so this migration is re-runnable
DROP TRIGGER IF EXISTS trg_candidates_updated_at ON candidates;
CREATE TRIGGER trg_candidates_updated_at
    BEFORE UPDATE ON candidates
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

DROP TRIGGER IF EXISTS trg_verified_leads_updated_at ON verified_leads;
CREATE TRIGGER trg_verified_leads_updated_at
    BEFORE UPDATE ON verified_leads
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

DROP TRIGGER IF EXISTS trg_packs_updated_at ON packs;
CREATE TRIGGER trg_packs_updated_at
    BEFORE UPDATE ON packs
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
