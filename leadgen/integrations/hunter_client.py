import os
import time
import logging
from typing import Optional, Dict, Any

import requests

logger = logging.getLogger(__name__)


class HunterClient:
    BASE_URL = os.getenv("HUNTER_BASE_URL", "https://api.hunter.io/v2")

    def __init__(self, api_key: Optional[str] = None, rate_limit_seconds: float = 0.0, base_url: Optional[str] = None):
        self.api_key = api_key or os.getenv("HUNTER_API_KEY")
        if base_url:
            self.BASE_URL = base_url
        env_rate_limit = os.getenv("HUNTER_RATE_LIMIT_SECONDS")
        if env_rate_limit:
            try:
                rate_limit_seconds = float(env_rate_limit)
            except ValueError:
                pass
        self.rate_limit_seconds = rate_limit_seconds
        self._last_call: Optional[float] = None

    def _maybe_sleep(self):
        if self._last_call is None:
            return
        elapsed = time.time() - self._last_call
        if self.rate_limit_seconds and elapsed < self.rate_limit_seconds:
            time.sleep(self.rate_limit_seconds - elapsed)

    def _error(self, resp, default_msg: str):
        err = {"error": default_msg}
        if resp.status_code == 429:
            err["rate_limited"] = True
            retry_after = resp.headers.get("Retry-After")
            if retry_after:
                try:
                    err["retry_after"] = int(retry_after)
                except ValueError:
                    pass
        err["status_code"] = resp.status_code
        return err

    def domain_search(self, domain: str, limit: int = 5) -> Dict[str, Any]:
        if not self.api_key:
            return {"error": "missing hunter api key"}
        self._maybe_sleep()
        try:
            resp = requests.get(
                f"{self.BASE_URL}/domain-search",
                params={"domain": domain, "limit": limit, "api_key": self.api_key},
                timeout=10,
            )
            self._last_call = time.time()
            if resp.status_code != 200:
                return self._error(resp, f"status {resp.status_code}")
            return resp.json()
        except ValueError:
            return {"error": "invalid json"}
        except Exception as exc:  # pragma: no cover - defensive
            return {"error": str(exc)}

    def verify_email(self, email: str) -> Dict[str, Any]:
        if not self.api_key:
            return {"error": "missing hunter api key"}
        self._maybe_sleep()
        try:
            resp = requests.get(
                f"{self.BASE_URL}/email-verifier",
                params={"email": email, "api_key": self.api_key},
                timeout=10,
            )
            self._last_call = time.time()
            if resp.status_code != 200:
                return self._error(resp, f"status {resp.status_code}")
            return resp.json()
        except ValueError:
            return {"error": "invalid json"}
        except Exception as exc:  # pragma: no cover
            return {"error": str(exc)}


def hunter_domain_search(domain: str, client: Optional[HunterClient] = None, limit: int = 5) -> Optional[Dict[str, Any]]:
    client = client or HunterClient()
    if not getattr(client, "api_key", None):
        logger.warning("hunter_domain_search skipped: missing api key")
        return None
    result = client.domain_search(domain, limit=limit)
    if result and not result.get("error"):
        return result
    logger.warning("hunter_domain_search failed for %s: %s", domain, result.get("error") if isinstance(result, dict) else "unknown")
    return None


def hunter_email_finder(domain: str, first_name: str, last_name: str, client: Optional[HunterClient] = None) -> Optional[Dict[str, Any]]:
    client = client or HunterClient()
    if not getattr(client, "api_key", None):
        logger.warning("hunter_email_finder skipped: missing api key")
        return None
    client._maybe_sleep()
    try:
        resp = requests.get(
            f"{client.BASE_URL}/email-finder",
            params={"domain": domain, "first_name": first_name, "last_name": last_name, "api_key": client.api_key},
            timeout=10,
        )
        client._last_call = time.time()
        if resp.status_code != 200:
            logger.warning("hunter_email_finder status %s for %s", resp.status_code, domain)
            return None
        data = resp.json()
        return {
            "email": data.get("data", {}).get("email"),
            "score": data.get("data", {}).get("score"),
            "domain": domain,
        }
    except Exception as exc:  # pragma: no cover
        logger.warning("hunter_email_finder error for %s: %s", domain, exc)
        return None
