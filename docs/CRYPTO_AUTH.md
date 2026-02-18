# Crypto Wallet Auth & Coinbase Payments (Backend)

## Endpoints
- `POST /auth/wallet/nonce` → returns nonce for wallet signing
- `POST /auth/wallet/verify` → verifies signature/nonce, issues session_token
- `POST /auth/wallet/session/validate` → validates existing session
- `POST /crypto/create-charge` → creates Coinbase Commerce charge (basic/enriched packs, domain scan)
- `POST /crypto/verify-webhook` → verifies Coinbase webhook (charge:confirmed)
- `GET /crypto/charge-status/{charge_id}` → poll charge status

## Env vars
- `COINBASE_API_KEY`
- `COINBASE_WEBHOOK_SECRET`
- `WALLET_AUTH_DB` (optional path for SQLite)

## Notes
- Signature verification uses placeholders; tests mock verification.
- Rate limits/analytics unchanged; no frontend integration yet.
- Use test keys for Coinbase during development.
