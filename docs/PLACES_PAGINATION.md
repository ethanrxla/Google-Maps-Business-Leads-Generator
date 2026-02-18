# Google Places Pagination

The lead generator now supports fetching more than one page from Google Places Text Search.

## Behavior
- Entry point: `leadgen.places.search_places(query, limit=20, include_status=False)`
- Uses Text Search endpoint: `https://maps.googleapis.com/maps/api/place/textsearch/json`
- Pagination:
  - Collects first page.
  - If `next_page_token` is present and we still need more results, waits ~2s and fetches the next page with `pagetoken`.
  - Repeats until `limit` reached, no token remains, or an error occurs.
- Limits:
  - Each page: up to 20 results (Google constraint).
  - Global cap: `MAX_PLACES_RESULTS = 1000`.
  - `limit` is clamped to this cap; default still 20.
- Errors/quotas:
  - On HTTP errors or non-OK statuses, returns whatever has been collected so far (soft-fail).

## Key constants (leadgen/places.py)
- `PLACES_PAGE_SIZE = 20`
- `MAX_PLACES_RESULTS = 1000`
- `PLACES_NEXT_PAGE_SLEEP_S = 2.0` (delay required for `next_page_token`)

## Downstream
- `leadgen.generator.generate_pack` passes `limit` through unchanged. Frontend still requests 20 by default, but the backend can now serve larger limits for future products (e.g., 50/100/500).
