import os
import time
import logging
from typing import Any, Dict, Optional, List

import requests

logger = logging.getLogger(__name__)


class ApolloClient:
    BASE_URL = os.getenv("APOLLO_BASE_URL", "https://api.apollo.io/v1")

    def __init__(self, api_key: Optional[str] = None, rate_limit_seconds: float = 0.0, base_url: Optional[str] = None):
        self.api_key = api_key or os.getenv("APOLLO_API_KEY")
        if base_url:
            self.BASE_URL = base_url
        env_rate_limit = os.getenv("APOLLO_RATE_LIMIT_SECONDS")
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

    def _headers(self) -> Dict[str, str]:
        headers = {"Content-Type": "application/json", "Cache-Control": "no-cache"}
        if self.api_key:
            headers["X-Api-Key"] = self.api_key
            headers["Authorization"] = f"Bearer {self.api_key}"
        return headers

    def enrich_person_by_email(
        self,
        email: str,
        first_name: Optional[str] = None,
        last_name: Optional[str] = None,
        organization_name: Optional[str] = None,
        domain: Optional[str] = None,
    ) -> Dict[str, Any]:
        if not self.api_key:
            return {"error": "missing apollo api key"}
        self._maybe_sleep()
        payload: Dict[str, Any] = {"email": email}
        if first_name:
            payload["first_name"] = first_name
        if last_name:
            payload["last_name"] = last_name
        if organization_name:
            payload["organization_name"] = organization_name
        if domain:
            payload["domain"] = domain
        try:
            resp = requests.post(
                f"{self.BASE_URL}/mixed_people/match",
                headers=self._headers(),
                json=payload,
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

    def enrich_company_by_domain(self, domain: str, organization_name: Optional[str] = None) -> Dict[str, Any]:
        if not self.api_key:
            return {"error": "missing apollo api key"}
        self._maybe_sleep()
        payload: Dict[str, Any] = {"domain": domain}
        if organization_name:
            payload["organization_name"] = organization_name
        try:
            resp = requests.post(
                f"{self.BASE_URL}/mixed_people/match_organization",
                headers=self._headers(),
                json=payload,
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


def apollo_bulk_org_enrich(domains: List[str], client: Optional[ApolloClient] = None) -> Dict[str, Dict[str, Any]]:
    client = client or ApolloClient()
    api_key = getattr(client, "api_key", None)
    base_url = getattr(client, "BASE_URL", None) or os.getenv("APOLLO_BASE_URL", "https://api.apollo.io/v1")
    if not api_key or not domains:
        logger.info("apollo_bulk_org_enrich skipped: missing api key or domains")
        return {}
    results: Dict[str, Dict[str, Any]] = {}
    try:
        resp = requests.post(
            f"{base_url}/organizations/bulk_enrich",
            headers=client._headers(),
            json={"domains": domains, "api_key": api_key},
            timeout=10,
        )
        client._last_call = time.time()
        if resp.status_code != 200:
            logger.warning("apollo_bulk_org_enrich status %s", resp.status_code)
            return {}
        data = resp.json()
        for org in data.get("organizations", []):
            domain = (org.get("domain") or "").lower()
            if domain:
                results[domain] = org
    except Exception as exc:  # pragma: no cover
        logger.warning("apollo_bulk_org_enrich error: %s", exc)
    return results


def apollo_get_org_job_postings(org_id: str, client: Optional[ApolloClient] = None) -> Optional[Dict[str, Any]]:
    client = client or ApolloClient()
    api_key = getattr(client, "api_key", None)
    base_url = getattr(client, "BASE_URL", None) or os.getenv("APOLLO_BASE_URL", "https://api.apollo.io/v1")
    if not api_key or not org_id:
        return None
    try:
        resp = requests.get(
            f"{base_url}/organizations/{org_id}/job_postings",
            headers=client._headers(),
            params={"api_key": api_key},
            timeout=10,
        )
        client._last_call = time.time()
        if resp.status_code != 200:
            logger.warning("apollo_get_org_job_postings status %s", resp.status_code)
            return None
        data = resp.json()
        postings = data.get("job_postings") or data.get("job_postings_list") or []
        count = len(postings)
        return {"count": count, "is_hiring": count > 0}
    except Exception as exc:  # pragma: no cover
        logger.warning("apollo_get_org_job_postings error: %s", exc)
        return None
