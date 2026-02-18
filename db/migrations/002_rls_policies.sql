-- Migration 002: Row Level Security policies for all pipeline tables.
--
-- Matches spec Section 7: service_role gets full access, anon can only
-- view sellable packs (storefront).  Uses DROP POLICY IF EXISTS before
-- each CREATE POLICY for idempotency.

-- ============================================================================
-- ENABLE RLS
-- ============================================================================
ALTER TABLE candidates ENABLE ROW LEVEL SECURITY;
ALTER TABLE verified_leads ENABLE ROW LEVEL SECURITY;
ALTER TABLE packs ENABLE ROW LEVEL SECURITY;
ALTER TABLE pack_entries ENABLE ROW LEVEL SECURITY;
ALTER TABLE pipeline_events ENABLE ROW LEVEL SECURITY;
ALTER TABLE batch_runs ENABLE ROW LEVEL SECURITY;

-- ============================================================================
-- SERVICE ROLE — full access on all tables
-- ============================================================================
DROP POLICY IF EXISTS "service_full" ON candidates;
CREATE POLICY "service_full" ON candidates FOR ALL USING (auth.role() = 'service_role');

DROP POLICY IF EXISTS "service_full" ON verified_leads;
CREATE POLICY "service_full" ON verified_leads FOR ALL USING (auth.role() = 'service_role');

DROP POLICY IF EXISTS "service_full" ON packs;
CREATE POLICY "service_full" ON packs FOR ALL USING (auth.role() = 'service_role');

DROP POLICY IF EXISTS "service_full" ON pack_entries;
CREATE POLICY "service_full" ON pack_entries FOR ALL USING (auth.role() = 'service_role');

DROP POLICY IF EXISTS "service_full" ON pipeline_events;
CREATE POLICY "service_full" ON pipeline_events FOR ALL USING (auth.role() = 'service_role');

DROP POLICY IF EXISTS "service_full" ON batch_runs;
CREATE POLICY "service_full" ON batch_runs FOR ALL USING (auth.role() = 'service_role');

-- ============================================================================
-- ANON — read-only access to sellable packs (storefront)
-- ============================================================================
DROP POLICY IF EXISTS "anon_sellable_packs" ON packs;
CREATE POLICY "anon_sellable_packs" ON packs FOR SELECT USING (sellable = TRUE);
