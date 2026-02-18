import os
from dataclasses import dataclass

from dotenv import load_dotenv

load_dotenv()


@dataclass
class BackendConfig:
    stripe_secret_key: str | None
    stripe_secret_key_test: str | None
    stripe_webhook_secret: str | None
    stripe_price_id: str | None
    stripe_price_id_basic: str | None
    stripe_price_id_basic_20: str | None
    stripe_price_id_basic_100: str | None
    stripe_price_id_basic_500: str | None
    stripe_price_id_basic_1000: str | None
    stripe_price_id_enriched: str | None
    stripe_mode: str | None
    frontend_base_url: str | None
    coinbase_api_key: str | None
    coinbase_webhook_secret: str | None
    builtwith_api_key: str | None
    scrapingbee_api_key: str | None
    apollo_api_key: str | None = None
    hunter_api_key: str | None = None
    apollo_base_url: str = "https://api.apollo.io/api/v1"
    hunter_base_url: str = "https://api.hunter.io/v2"


config = BackendConfig(
    stripe_secret_key=os.getenv("STRIPE_SECRET_KEY"),
    stripe_secret_key_test=os.getenv("STRIPE_SECRET_KEY_TEST"),
    stripe_webhook_secret=os.getenv("STRIPE_WEBHOOK_SECRET"),
    stripe_price_id=os.getenv("STRIPE_PRICE_ID"),
    stripe_price_id_basic=os.getenv("STRIPE_PRICE_ID_BASIC"),
    # Allow both new BASIC_* and legacy *_N naming for raw packs
    stripe_price_id_basic_20=os.getenv("STRIPE_PRICE_ID_BASIC_20") or os.getenv("STRIPE_PRICE_ID_20") or os.getenv("STRIPE_PRICE_ID"),
    stripe_price_id_basic_100=os.getenv("STRIPE_PRICE_ID_BASIC_100") or os.getenv("STRIPE_PRICE_ID_100"),
    stripe_price_id_basic_500=os.getenv("STRIPE_PRICE_ID_BASIC_500") or os.getenv("STRIPE_PRICE_ID_500"),
    stripe_price_id_basic_1000=os.getenv("STRIPE_PRICE_ID_BASIC_1000") or os.getenv("STRIPE_PRICE_ID_1000"),
    stripe_price_id_enriched=os.getenv("STRIPE_PRICE_ID_ENRICHED"),
    stripe_mode=os.getenv("STRIPE_MODE"),
    frontend_base_url=os.getenv("FRONTEND_BASE_URL"),
    coinbase_api_key=os.getenv("COINBASE_API_KEY"),
    coinbase_webhook_secret=os.getenv("COINBASE_WEBHOOK_SECRET"),
    builtwith_api_key=os.getenv("BUILTWITH_API_KEY"),
    scrapingbee_api_key=os.getenv("SCRAPINGBEE_API_KEY"),
    apollo_api_key=os.getenv("APOLLO_API_KEY"),
    hunter_api_key=os.getenv("HUNTER_API_KEY"),
    apollo_base_url=os.getenv("APOLLO_BASE_URL", "https://api.apollo.io/api/v1"),
    hunter_base_url=os.getenv("HUNTER_BASE_URL", "https://api.hunter.io/v2"),
)
