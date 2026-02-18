import { BACKEND_BASE_URL } from './config';
import type { FeaturedPackConfig } from './featured-packs';

export interface StartPackRequest {
  pack_id?: string;
  query: string;
  country: string | null;
  state: string | null;
  county: string | null;
  city: string;
  niche: string | null;
  limit: number;
  enrichment_tier?: 'basic_pack' | 'enriched_pack';
}

export interface StartPackResponse {
  checkout_url: string;
  pack_id: string;
}

export async function startPack(request: StartPackRequest): Promise<StartPackResponse> {
  const response = await fetch(`${BACKEND_BASE_URL}/start-pack`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify(request),
  });

  if (!response.ok) {
    throw new Error(`Failed to start pack: ${response.statusText}`);
  }

  return response.json();
}

export async function startFeaturedPack(
  pack: FeaturedPackConfig,
  product_type: 'basic_pack' | 'enriched_pack',
  lead_count?: number
): Promise<StartPackResponse> {
  const payload: StartPackRequest = {
    pack_id: pack.id,
    query: pack.query,
    country: pack.country,
    state: pack.state,
    county: pack.county || null,
    city: pack.city,
    niche: pack.niche,
    limit: lead_count ?? pack.limit,
    enrichment_tier: product_type,
  };
  return startPack(payload);
}

export type DownloadFormat = 'csv' | 'jsonl' | 'json' | 'xml';

export function getDownloadUrl(sessionId: string, format: DownloadFormat): string {
  return `${BACKEND_BASE_URL}/download-pack?session_id=${sessionId}&format=${format}`;
}

export async function getDownloadInfo(sessionId: string): Promise<{
  pack_id: string;
  is_harvest: boolean;
  formats: DownloadFormat[];
}> {
  const resp = await fetch(`${BACKEND_BASE_URL}/download-info?session_id=${sessionId}`);
  if (!resp.ok) {
    throw new Error(`Failed to fetch download info: ${resp.statusText}`);
  }
  return resp.json();
}
