import os
from typing import Any, Dict, Optional

import requests


class BuiltWithClient:
    BASE_URL = "https://api.builtwith.com/v20/api.json"

    def __init__(self, api_key: Optional[str] = None, timeout: int = 10):
        self.api_key = api_key or os.getenv("BUILTWITH_API_KEY")
        self.timeout = timeout

    def tech_lookup(self, domain: str) -> Optional[Dict[str, Any]]:
        if not self.api_key or not domain:
            return None
        try:
            resp = requests.get(
                self.BASE_URL,
                params={"KEY": self.api_key, "LOOKUP": domain},
                timeout=self.timeout,
            )
            if resp.status_code != 200:
                return None
            return resp.json()
        except Exception:
            return None
