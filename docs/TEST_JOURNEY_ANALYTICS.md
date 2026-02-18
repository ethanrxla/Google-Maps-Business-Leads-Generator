# Test Journey: Analytics, Checkout, and Domain Scan

## Prereqs
- Backend running: `uvicorn backend.server:app --reload`
- Frontend running: `npm run dev` from `frontend/project`
- .env: `STRIPE_MODE=test` with test keys; `NEXT_PUBLIC_BACKEND_URL=http://localhost:8000`

## Steps
1) Visit landing page (`/`)
   - Cookie consent banner appears. Accept analytics.
   - Page view tracked (POST /analytics/event).

2) Add pack to cart (basic or enriched)
   - Event: `pack_purchase_started` sent from frontend.

3) Start checkout
   - Event dispatched; Stripe Checkout URL returned.

4) Complete Stripe checkout (test mode)
   - Use test card `4242 4242 4242 4242` (any future expansion cards apply).
   - Backend logs checkout success via Stripe webhook/redirect.

5) Download pack
   - Event: download/fulfillment tracked.

6) Domain scan (manual)
   - `curl -X POST http://127.0.0.1:8000/harvest-domain -H 'Content-Type: application/json' -d '{"domain":"example.com","sources":["google","bing"],"limit":50}'`
   - Expect JSON with status, raw_output_path, lines_in_raw.

7) WSL manual scan
   - `python -m harvest.src.core.wsl_harvester -d example.com -s "google,bing" -l 50`
   - Check raw output under `harvest/src/data/outputs/leads/raw_leads/` and exports.

Notes: analytics opt-out via cookie_preference.analytics=false prevents events. Stripe test mode never charges real cards.
