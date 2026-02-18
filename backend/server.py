import json
from pathlib import Path
import sys
from datetime import datetime
from typing import Any, Dict, List
import sqlite3
import time
import uuid
import logging
import yaml

# --- Logger Setup ---
logger = logging.getLogger("backend")
logger.setLevel(logging.INFO)
if not logger.handlers:
    handler = logging.StreamHandler(sys.stdout)
    formatter = logging.Formatter("[%(asctime)s] [%(levelname)s] %(message)s")
    handler.setFormatter(formatter)
    logger.addHandler(handler)
# --- End Logger Setup ---

try:
    import stripe  # type: ignore
except Exception as e:  # pragma: no cover - boot guard
    stripe = None

from backend import stripe_utils
from backend.config import config
from leadgen.packs_index import resolve_pack_files, list_packs
from leadgen.generator import make_pack_id
from leadgen.generator import slugify as _slugify
# Add harvest module to path for domain scanning
HARVEST_SRC = Path(__file__).resolve().parents[1] / "harvest" / "src"
if str(HARVEST_SRC) not in sys.path:
    sys.path.append(str(HARVEST_SRC))
from core.wsl_harvester import run_harvest_job  # type: ignore
from core.job_result import HarvestJobResult  # type: ignore
from backend.crypto_auth import (
    generate_nonce as crypto_generate_nonce,
    verify_signature as crypto_verify_signature,
    validate_session as crypto_validate_session,
)
from backend.coinbase_payments import (
    create_coinbase_charge,
    verify_coinbase_webhook,
    check_charge_status,
)

try:  # pragma: no cover - optional FastAPI
    from fastapi import FastAPI, HTTPException, Request
    from fastapi.middleware.cors import CORSMiddleware
    from fastapi.responses import FileResponse, JSONResponse
except ImportError:  # pragma: no cover
    FastAPI = None
    HTTPException = Exception
    JSONResponse = None
    FileResponse = None


def create_checkout_session_handler(body: Dict[str, Any]):
    pack_id = body.get("pack_id")
    if not pack_id:
        raise HTTPException(status_code=400, detail="pack_id is required")

    csv_path, jsonl_path = resolve_pack_files(pack_id)
    if not csv_path:
        raise HTTPException(status_code=404, detail="pack not found")

    if not config.frontend_base_url:
        raise HTTPException(status_code=500, detail="FRONTEND_BASE_URL not configured")

    success_url = f"{config.frontend_base_url}/success?session_id={{CHECKOUT_SESSION_ID}}"
    cancel_url = f"{config.frontend_base_url}/cancel"

    return stripe_utils.create_checkout_session(
        pack_id=pack_id,
        price_id=config.stripe_price_id,
        success_url=success_url,
        cancel_url=cancel_url,
    )


def webhook_handler(payload: bytes, sig_header: str):
    event = stripe_utils.verify_webhook_signature(payload, sig_header)

    if event["type"] == "checkout.session.completed":
        session = event["data"]["object"]
        pack_id = session.get("metadata", {}).get("pack_id")
        csv_path, jsonl_path = resolve_pack_files(pack_id) if pack_id else (None, None)
        # TODO: deliver files (email/signed URL). For now, log/print for visibility.
        logger.info(f"Deliver pack_id={pack_id} csv={csv_path} jsonl={jsonl_path}")
        return {"status": "delivered", "pack_id": pack_id, "csv": str(csv_path), "jsonl": str(jsonl_path)}

    return {"status": "ignored"}


if FastAPI:  # pragma: no cover
    app = FastAPI()

    @app.middleware("http")
    async def log_requests(request: Request, call_next):
        logger.info("REQUEST %s %s", request.method, request.url.path)
        response = await call_next(request)
        logger.info("RESPONSE %s %s -> %s", request.method, request.url.path, response.status_code)
        return response

    origins = [
        config.frontend_base_url,
        "http://localhost:3000",
    ]
    BASE_PRICE_BASIC = 1200
    BASE_PRICE_ENRICHED = 2400
    app.add_middleware(
        CORSMiddleware,
        allow_origins=[o for o in origins if o],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    @app.get("/")
    async def root():
        return {"status": "ok", "service": "leadgen-backend"}

    # Frontend contract:
    # After Stripe Checkout, Stripe redirects users to:
    #   {FRONTEND_BASE_URL}/success?session_id={CHECKOUT_SESSION_ID}
    # The frontend should call /download-pack?session_id=<session_id>&format=csv (or jsonl)
    # to retrieve the purchased lead pack files.

    @app.post("/create-checkout-session")
    async def create_checkout_session_route(body: Dict[str, Any]):
        try:
            result = create_checkout_session_handler(body)
            return JSONResponse(result)
        except HTTPException as exc:
            logger.exception("HTTPException in create_checkout_session_route")
            raise exc
        except Exception as exc:
            logger.exception("Unhandled exception in create_checkout_session_route")
            raise HTTPException(status_code=500, detail=str(exc))

    @app.post("/stripe/webhook")
    async def stripe_webhook_route(request):
        payload = await request.body()
        sig_header = request.headers.get("stripe-signature", "")
        try:
            result = webhook_handler(payload, sig_header)
            return JSONResponse(result)
        except HTTPException as exc:
            logger.exception("HTTPException in stripe_webhook_route")
            raise exc
        except Exception as exc:
            logger.exception("Unhandled exception in stripe_webhook_route")
            raise HTTPException(status_code=500, detail=str(exc))

    @app.get("/download-pack")
    async def download_pack(session_id: str, format: str = "csv"):
        """
        Verify a paid Stripe Checkout Session and stream the purchased pack file.
        For harvest (domain scan) sessions, transparently serve the JSON/XML output.
        """
        logger.info(f"Download request for session_id={session_id}, format={format}")
        if FileResponse is None:
            raise HTTPException(status_code=500, detail="FastAPI not installed")

        stripe_utils._require_stripe()  # type: ignore[attr-defined]
        session = stripe_utils.stripe.checkout.Session.retrieve(session_id)  # type: ignore[union-attr]
        if not session:
            raise HTTPException(status_code=400, detail="Invalid session")

        if session.get("payment_status") != "paid":
            logger.warning(f"Download attempt for unpaid session_id={session_id}")
            raise HTTPException(status_code=402, detail="Payment not completed")

        metadata = session.get("metadata") or {}
        pack_id = metadata.get("pack_id")
        if not pack_id:
            logger.error(f"Missing pack_id in session metadata for session_id={session_id}")
            raise HTTPException(status_code=400, detail="Missing pack_id")
        
        logger.info(f"Resolved pack_id={pack_id} for session_id={session_id}")

        is_harvest = pack_id.startswith("harvest-")
        if is_harvest:
            # Accept json/xml for harvest; if an unexpected format is requested, fall back to json.
            harvest_formats = {"json", "xml"}
            if format not in harvest_formats:
                logger.info("Harvest download requested with format=%s, falling back to json", format)
                format = "json"
            target = _resolve_harvest_file(pack_id, fmt=format)
            if not target or not target.exists():
                logger.error("Harvest file not found for pack_id=%s format=%s", pack_id, format)
                raise HTTPException(status_code=404, detail="Harvest file not found")
            media_type = "application/json" if format == "json" else "application/xml"
            filename = f"{pack_id}.{format}"
            logger.info("Streaming harvest file %s as %s", target, filename)
            return FileResponse(path=target, media_type=media_type, filename=filename)

        # Standard lead packs
        csv_path, jsonl_path = resolve_pack_files(pack_id, base_dir=Path("data/packs"))
        logger.info(
            "download_pack: session_id=%s pack_id=%s csv=%s jsonl=%s",
            session_id,
            pack_id,
            csv_path,
            jsonl_path,
        )

        if format not in ("csv", "jsonl"):
            raise HTTPException(status_code=400, detail="Invalid format")

        target_path = csv_path if format == "csv" else jsonl_path
        media_type = "text/csv" if format == "csv" else "application/json"

        if not target_path or not Path(target_path).exists():
            logger.error(f"Pack file not found for pack_id={pack_id}, format={format}")
            raise HTTPException(status_code=404, detail="Pack file not found")

        filename = f"{pack_id}.{format}"
        logger.info(f"Streaming file {target_path} as {filename}")
        return FileResponse(
            path=target_path,
            media_type=media_type,
            filename=filename,
        )

    @app.get("/download-info")
    async def download_info(session_id: str):
        """
        Return pack metadata and available download formats for a paid session.
        Helps the frontend decide which labels/links to show (pack vs harvest).
        """
        stripe_utils._require_stripe()  # type: ignore[attr-defined]
        session = stripe_utils.stripe.checkout.Session.retrieve(session_id)  # type: ignore[union-attr]
        if not session:
            raise HTTPException(status_code=400, detail="Invalid session")
        if session.get("payment_status") != "paid":
            raise HTTPException(status_code=402, detail="Payment not completed")

        metadata = session.get("metadata") or {}
        pack_id = metadata.get("pack_id")
        if not pack_id:
            raise HTTPException(status_code=400, detail="Missing pack_id")

        is_harvest = pack_id.startswith("harvest-")
        formats = ["json", "xml"] if is_harvest else ["csv", "jsonl"]
        return {"pack_id": pack_id, "is_harvest": is_harvest, "formats": formats}

    # Models for start-pack
    from pydantic import BaseModel, Field  # type: ignore

    class StartPackRequest(BaseModel):
        query: str
        country: str
        state: str | None = None
        county: str | None = None
        city: str
        niche: str | None = None
        limit: int = Field(default=50, ge=1, le=1000)
        enrichment_tier: str | None = "basic"

    class StartPackResponse(BaseModel):
        checkout_url: str
        pack_id: str
    class HarvestRequest(BaseModel):
        domain: str
        sources: list[str] | None = None
        limit: int | None = 100

    class HarvestResponse(BaseModel):
        domain: str
        status: str
        sources: list[str]
        limit: int
        started_at: str
        finished_at: str | None
        raw_output_path: str | None
        lines_in_raw: int
        error_message: str | None
        stdout: str | None = None
        stderr: str | None = None
        pack_id: str | None = None
        checkout_url: str | None = None

    class CartItem(BaseModel):
        pack_id: str
        enrichment_tier: str = "basic"
        quantity: int = 1

    class CartPayload(BaseModel):
        items: list[CartItem]

    class AnalyticsEvent(BaseModel):
        event_name: str
        user_id: str | None = None
        session_id: str
        properties: Dict[str, Any] = {}
        timestamp: str | None = None

    class AnalyticsSession(BaseModel):
        session_id: str
        user_id: str | None = None
        properties: Dict[str, Any] = {}

    class WalletNonceRequest(BaseModel):
        wallet_address: str
        chain: str

    class WalletVerifyRequest(BaseModel):
        wallet_address: str
        chain: str
        signature: str
        nonce: str

    class WalletSessionValidate(BaseModel):
        wallet_address: str
        session_token: str

    def start_pack_handler(payload: Dict[str, Any]):
        logger.info(f"start_pack_handler received payload: {payload}")
        if not config.frontend_base_url:
            raise HTTPException(status_code=500, detail="FRONTEND_BASE_URL not configured")

        query = payload.get("query")
        country = payload.get("country")
        city = payload.get("city")
        limit = payload.get("limit", 50)
        if not query or not country or not city:
            raise HTTPException(status_code=400, detail="query, country, and city are required")
        if not isinstance(limit, int) or limit < 1 or limit > 1000:
            raise HTTPException(status_code=400, detail="limit must be between 1 and 1000")

        pack_id = payload.get("pack_id")
        if not pack_id:
            pack_id = make_pack_id(
                country=country,
                state=payload.get("state"),
                county=payload.get("county"),
                city=city,
                niche=payload.get("niche"),
                limit=limit,
            )
            logger.info(f"Generated new pack_id: {pack_id}, generating pack...")
            from leadgen.generator import generate_pack
            summary = generate_pack(
                query=query,
                country=country,
                state=payload.get("state"),
                county=payload.get("county"),
                city=city,
                niche=payload.get("niche"),
                limit=limit,
                pack_id=pack_id,
            )
            if not summary.get("sellable", False):
                failures = summary.get("quality_gate_failures") or []
                reasons = "; ".join(str(x) for x in failures) if failures else "quality_gates_failed"
                raise HTTPException(
                    status_code=422,
                    detail=f"Pack failed quality gates and is not sellable: {reasons}",
                )
        logger.info(f"Using pack_id: {pack_id}")

        success_url = f"{config.frontend_base_url}/success?session_id={{CHECKOUT_SESSION_ID}}"
        cancel_url = f"{config.frontend_base_url}/cancel"

        enrichment_tier = (payload.get("enrichment_tier") or "basic").lower()
        logger.info(f"Enrichment tier: {enrichment_tier}")
        price_id = None
        if enrichment_tier == "enriched_pack":
            if config.stripe_price_id_enriched:
                price_id = config.stripe_price_id_enriched
            else:
                raise HTTPException(status_code=400, detail="Enriched pack is not available")
        else:
            try:
                price_id = stripe_utils.choose_basic_price_id(limit)
            except Exception as exc:
                logger.warning("Unsupported basic pack size: %s", limit)
                # Backward compatibility: allow arbitrary limits to use legacy/default
                # basic Stripe price when configured (older clients/tests depend on this).
                fallback_price = config.stripe_price_id_basic or config.stripe_price_id
                if fallback_price:
                    logger.info("Falling back to default basic price for unsupported limit=%s", limit)
                    price_id = fallback_price
                else:
                    raise HTTPException(status_code=400, detail="Unsupported lead pack size") from exc
        
        logger.info(f"Using price_id: {price_id} for pack_id: {pack_id}")
        session = stripe_utils.create_checkout_session(
            pack_id=pack_id,
            price_id=price_id,
            success_url=success_url,
            cancel_url=cancel_url,
        )

        return {"checkout_url": session["url"], "pack_id": pack_id}

    @app.post("/start-pack", response_model=StartPackResponse)
    async def start_pack_route(req: StartPackRequest):
        try:
            return start_pack_handler(req.model_dump())
        except HTTPException as exc:
            logger.exception("HTTPException in start_pack_route")
            raise exc
        except Exception as exc:
            logger.exception("Unhandled exception in start_pack_route")
            raise HTTPException(status_code=500, detail=str(exc))

    def _lines_in_file(path: str | None) -> int:
        if not path or not Path(path).exists():
            return 0
        return sum(1 for _ in Path(path).read_text().splitlines())

    def _resolve_harvest_file(pack_id: str, fmt: str = "json") -> Path | None:
        """
        Find the most recent harvest output file for the given pack_id.
        pack_id is "harvest-{slug}", where slug uses slugify(domain).
        Files are stored under harvest/src/data/outputs/leads/raw_leads
        and named like <domain_slug>_YYYYMMDD_HHMMSS.<ext>.
        """
        domain_part = pack_id.replace("harvest-", "", 1)
        slug = domain_part.replace("-", "_")
        raw_dir = Path("harvest/src/data/outputs/leads/raw_leads")
        if not raw_dir.exists():
            return None
        candidates = sorted(raw_dir.glob(f"{slug}*.{fmt}"), key=lambda p: p.stat().st_mtime, reverse=True)
        return candidates[0] if candidates else None

    @app.get("/download-harvest")
    async def download_harvest(session_id: str, format: str = "json"):
        """
        Verify paid session and stream harvest output (json or xml).
        """
        logger.info("download_harvest session_id=%s format=%s", session_id, format)
        if FileResponse is None:
            raise HTTPException(status_code=500, detail="FastAPI not installed")
        if format not in ("json", "xml"):
            raise HTTPException(status_code=400, detail="Invalid format")

        stripe_utils._require_stripe()  # type: ignore[attr-defined]
        session = stripe_utils.stripe.checkout.Session.retrieve(session_id)  # type: ignore[union-attr]
        if not session:
            raise HTTPException(status_code=400, detail="Invalid session")
        if session.get("payment_status") != "paid":
            logger.warning("Harvest download attempt for unpaid session_id=%s", session_id)
            raise HTTPException(status_code=402, detail="Payment not completed")

        metadata = session.get("metadata") or {}
        pack_id = metadata.get("pack_id")
        if not pack_id or not pack_id.startswith("harvest-"):
            logger.error("Missing or invalid pack_id in harvest session metadata: %s", pack_id)
            raise HTTPException(status_code=400, detail="Missing harvest pack_id")

        target = _resolve_harvest_file(pack_id, fmt=format)
        if not target or not target.exists():
            logger.error("Harvest file not found for pack_id=%s format=%s", pack_id, format)
            raise HTTPException(status_code=404, detail="Harvest file not found")

        media_type = "application/json" if format == "json" else "application/xml"
        filename = f"{pack_id}.{format}"
        logger.info("Streaming harvest file %s as %s", target, filename)
        return FileResponse(path=target, media_type=media_type, filename=filename)

    # --- Analytics setup ---
    ANALYTICS_DB = Path("backend/analytics.db")
    RATE_LIMIT = 10  # events per minute per IP
    _rate_limit_store: Dict[str, List[float]] = {}

    def _init_analytics_db():
        ANALYTICS_DB.parent.mkdir(parents=True, exist_ok=True)
        conn = sqlite3.connect(ANALYTICS_DB)
        cur = conn.cursor()
        cur.execute(
            """
            CREATE TABLE IF NOT EXISTS analytics_events (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                session_id TEXT,
                event_name TEXT,
                properties TEXT,
                timestamp TEXT,
                user_agent TEXT,
                ip TEXT
            )
            """
        )
        conn.commit()
        conn.close()

    _init_analytics_db()

    def _rate_limited(ip: str) -> bool:
        now = time.time()
        window_start = now - 60
        entries = _rate_limit_store.get(ip, [])
        entries = [t for t in entries if t >= window_start]
        if len(entries) >= RATE_LIMIT:
            _rate_limit_store[ip] = entries
            return True
        entries.append(now)
        _rate_limit_store[ip] = entries
        return False

    @app.post("/auth/wallet/nonce")
    async def wallet_nonce(req: WalletNonceRequest):
        if not req.wallet_address:
            raise HTTPException(status_code=400, detail="wallet_address required")
        nonce = crypto_generate_nonce(req.wallet_address, req.chain)
        return {"nonce": nonce}

    @app.post("/auth/wallet/verify")
    async def wallet_verify(req: WalletVerifyRequest):
        res = crypto_verify_signature(req.wallet_address, req.signature, req.nonce, req.chain)
        if not res:
            raise HTTPException(status_code=400, detail="invalid signature or nonce")
        return res

    @app.post("/auth/wallet/session/validate")
    async def wallet_session_validate(req: WalletSessionValidate):
        if crypto_validate_session(req.session_token, req.wallet_address):
            return {"status": "valid"}
        raise HTTPException(status_code=401, detail="invalid session")

    @app.post("/harvest-domain", response_model=HarvestResponse)
    async def harvest_domain_route(req: HarvestRequest):
        if not req.domain:
            raise HTTPException(status_code=400, detail="domain is required")

        harvest_cfg = None
        cfg_path = Path("harvest/config.yaml")
        if cfg_path.exists():
            try:
                harvest_cfg = yaml.safe_load(cfg_path.read_text())
            except Exception:
                harvest_cfg = None

        allowed_sources = ["duckduckgo", "crtsh"]  # keep sources aligned with working CLI
        default_sources = allowed_sources
        cfg_sources = (harvest_cfg or {}).get("theharvester", {}).get("sources")
        sources_in = req.sources or cfg_sources or default_sources
        if sources_in == ["all"] or sources_in == "all":  # type: ignore[comparison-overlap]
            sources = default_sources
        else:
            sources = [s for s in sources_in if s in allowed_sources]
            if not sources:
                sources = default_sources
        logger.info("harvest.start", extra={"domain": req.domain, "sources": sources, "limit": req.limit})
        pack_id = f"harvest-{_slugify(req.domain)}"
        result: HarvestJobResult = run_harvest_job(
            domain=req.domain,
            sources=sources,
            limit=req.limit or 100,
            output_base=Path("harvest/src/data/outputs/leads"),
            export_windows=False,
            config=harvest_cfg,
        )

        checkout_url: str | None = None
        if result.status != "success":
            logger.warning("harvest.error", extra={"domain": req.domain, "error": result.error_message})
            logger.debug("harvest.stdout: %s", result.stdout)
            logger.debug("harvest.stderr: %s", result.stderr)
        else:
            # Offer checkout for domain scan results when Stripe is configured
            if config.frontend_base_url and config.stripe_price_id:
                try:
                    success_url = f"{config.frontend_base_url}/success?session_id={{CHECKOUT_SESSION_ID}}"
                    cancel_url = f"{config.frontend_base_url}/cancel"
                    session = stripe_utils.create_checkout_session(
                        pack_id=pack_id,
                        price_id=config.stripe_price_id,
                        success_url=success_url,
                        cancel_url=cancel_url,
                    )
                    checkout_url = session.get("url")
                except Exception as exc:  # pragma: no cover - defensive guard
                    logger.warning("harvest.checkout_failed", exc_info=exc)
        status_label = "completed" if result.status == "success" else "error"
        return {
            "domain": result.domain,
            "status": status_label,
            "sources": result.sources,
            "limit": result.limit,
            "started_at": result.started_at.isoformat(),
            "finished_at": result.finished_at.isoformat() if result.finished_at else None,
            "raw_output_path": result.raw_output_path,
            "lines_in_raw": _lines_in_file(result.raw_output_path),
            "error_message": result.error_message,
            "stdout": result.stdout,
            "stderr": result.stderr,
            "pack_id": pack_id,
            "checkout_url": checkout_url,
        }

    def calculate_cart_line_items(items: list[Dict[str, Any]]):
        flat_items = []
        for item in items:
            qty = item.get("quantity", 1) or 1
            for _ in range(qty):
                flat_items.append(
                    {
                        "pack_id": item.get("pack_id"),
                        "enrichment_tier": (item.get("enrichment_tier") or "basic").lower(),
                    }
                )
        line_items = []
        for idx, entry in enumerate(flat_items, start=1):
            tier = entry["enrichment_tier"]
            base_amount = BASE_PRICE_BASIC if tier == "basic" else BASE_PRICE_ENRICHED
            amount = base_amount
            if idx % 3 == 0:
                amount = int(base_amount * 0.5)
            line_items.append(
                {
                    "price_data": {
                        "currency": "usd",
                        "unit_amount": amount,
                        "product_data": {"name": f"{tier} pack ({entry['pack_id']})"},
                    },
                    "quantity": 1,
                    "metadata": {"pack_id": entry["pack_id"], "enrichment_tier": tier},
                }
            )
        return line_items

    @app.post("/create-cart-checkout")
    async def create_cart_checkout(payload: CartPayload):
        if not config.frontend_base_url:
            raise HTTPException(status_code=500, detail="FRONTEND_BASE_URL not configured")
        if not payload.items:
            raise HTTPException(status_code=400, detail="No items provided")

        line_items = calculate_cart_line_items([item.model_dump() for item in payload.items])
        stripe_utils._require_stripe()  # type: ignore[attr-defined]
        session = stripe_utils.stripe.checkout.Session.create(  # type: ignore[union-attr]
            mode="payment",
            line_items=line_items,
            success_url=f"{config.frontend_base_url}/success?session_id={{CHECKOUT_SESSION_ID}}",
            cancel_url=f"{config.frontend_base_url}/cancel",
        )
        return {"checkout_url": session["url"], "session_id": session.get("id")}

    def _analytics_opted_out(request) -> bool:
        cookie = request.cookies.get("cookie_preference")
        if not cookie:
            return False
        try:
            data = json.loads(cookie)
            return data.get("analytics") is False
        except Exception:
            return False

    def _record_event(event: AnalyticsEvent, request):
        if _analytics_opted_out(request):
            return False
        ip = request.client.host if request and request.client else "unknown"
        if _rate_limited(ip):
            raise HTTPException(status_code=429, detail="Rate limit exceeded")
        ua = request.headers.get("user-agent", "") if request else ""
        conn = sqlite3.connect(ANALYTICS_DB)
        cur = conn.cursor()
        cur.execute(
            "INSERT INTO analytics_events (session_id, event_name, properties, timestamp, user_agent, ip) VALUES (?, ?, ?, ?, ?, ?)",
            (
                event.session_id,
                event.event_name,
                json.dumps(event.properties or {}),
                event.timestamp or datetime.utcnow().isoformat(),
                ua,
                ip,
            ),
        )
        conn.commit()
        conn.close()
        return True

    @app.post("/analytics/event")
    async def analytics_event(req: AnalyticsEvent, request: Request):
        if not req.event_name or not req.session_id:
            raise HTTPException(status_code=400, detail="event_name and session_id required")
        try:
            _record_event(req, request)
            return {"status": "ok"}
        except HTTPException as exc:
            raise exc
        except Exception as exc:  # pragma: no cover
            raise HTTPException(status_code=500, detail=str(exc))

    @app.post("/analytics/session")
    async def analytics_session(req: AnalyticsSession, request: Request):
        ev = AnalyticsEvent(event_name="session_start", session_id=req.session_id, properties=req.properties)
        _record_event(ev, request)
        return {"status": "ok"}

    @app.post("/crypto/create-charge")
    async def crypto_create_charge(body: Dict[str, Any]):
        product_type = body.get("product_type")
        pack_id = body.get("pack_id")
        if not product_type:
            raise HTTPException(status_code=400, detail="product_type required")

        price_map = {
            "basic_pack": 12,
            "enriched_pack": 24,
            "domain_scan": 7,
        }
        price = price_map.get(product_type)
        if price is None:
            raise HTTPException(status_code=400, detail="unknown product_type")

        metadata = {"product_type": product_type, "pack_id": pack_id}
        charge = create_coinbase_charge(product_type, price, metadata)
        if "error" in charge:
            raise HTTPException(status_code=500, detail=charge["error"])
        return {"checkout_url": charge.get("hosted_url"), "charge_id": charge.get("charge_id")}

    @app.post("/crypto/verify-webhook")
    async def crypto_verify_webhook(request):
        body = await request.body()
        event = verify_coinbase_webhook(request.headers, body)
        if not event:
            raise HTTPException(status_code=400, detail="invalid signature")
        event_type = event.get("event", {}).get("type")
        if event_type != "charge:confirmed":
            return {"status": "ignored"}
        return {"status": "processed"}

    @app.get("/crypto/charge-status/{charge_id}")
    async def crypto_charge_status(charge_id: str):
        status = check_charge_status(charge_id)
        return status

    @app.get("/admin/packs")
    async def admin_list_packs():
        """
        Return a JSON list of available lead packs on disk.
        TODO: Restrict access (API key/auth) before production use.
        """
        try:
            packs = list_packs()
        except Exception as exc:  # pragma: no cover - defensive
            raise HTTPException(status_code=500, detail="Failed to list packs") from exc
        return {"packs": packs}

    # --- Pipeline endpoints ---

    class PipelineBatchRequest(BaseModel):
        batch_type: str = "city_sweep"
        query: str
        city: str
        state: str | None = None
        country: str = "US"
        niche: str | None = None
        limit: int = Field(default=50, ge=1, le=1000)
        enrichment_tier: str = "basic"

    def pipeline_batch_handler(payload: Dict[str, Any]) -> Dict[str, Any]:
        from pipeline.orchestrator import run_batch
        return run_batch(
            batch_type=payload.get("batch_type", "city_sweep"),
            query=payload["query"],
            city=payload["city"],
            state=payload.get("state"),
            country=payload.get("country", "US"),
            niche=payload.get("niche"),
            limit=payload.get("limit", 50),
            enrichment_tier=payload.get("enrichment_tier", "basic"),
        )

    @app.post("/pipeline/batch")
    async def pipeline_batch_route(req: PipelineBatchRequest):
        try:
            result = pipeline_batch_handler(req.model_dump())
            return JSONResponse(result)
        except HTTPException as exc:
            raise exc
        except Exception as exc:
            logger.exception("pipeline_batch_route error")
            raise HTTPException(status_code=500, detail=str(exc))

    def pipeline_batch_status_handler(batch_id: str) -> Dict[str, Any]:
        from db.repositories import get_batch_run
        run = get_batch_run(batch_id)
        if not run:
            raise HTTPException(status_code=404, detail="Batch not found")
        return run

    @app.get("/pipeline/batch/{batch_id}")
    async def pipeline_batch_status_route(batch_id: str):
        try:
            result = pipeline_batch_status_handler(batch_id)
            return JSONResponse(result)
        except HTTPException as exc:
            raise exc
        except Exception as exc:
            logger.exception("pipeline_batch_status_route error")
            raise HTTPException(status_code=500, detail=str(exc))

    def pipeline_stats_handler() -> Dict[str, Any]:
        from db.repositories import count_candidates, count_verified_leads
        from db.repositories import get_sellable_packs
        return {
            "total_candidates": count_candidates(),
            "total_verified": count_verified_leads(),
            "sellable_packs": len(get_sellable_packs()),
        }

    @app.get("/pipeline/stats")
    async def pipeline_stats_route():
        try:
            result = pipeline_stats_handler()
            return JSONResponse(result)
        except Exception as exc:
            logger.exception("pipeline_stats_route error")
            raise HTTPException(status_code=500, detail=str(exc))

else:  # pragma: no cover
    app = FastAPI()
