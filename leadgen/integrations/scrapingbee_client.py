import os
from typing import Optional

import requests


class ScrapingBeeClient:
    BASE_URL = "https://app.scrapingbee.com/api/v1/"

    def __init__(self, api_key: Optional[str] = None, timeout: int = 12):
        self.api_key = api_key or os.getenv("SCRAPINGBEE_API_KEY")
        self.timeout = timeout

    def fetch(self, url: str) -> Optional[str]:
        if not self.api_key or not url:
            return None
        try:
            resp = requests.get(
                self.BASE_URL,
                params={
                    "api_key": self.api_key,
                    "url": url,
                    "render_js": "true",
                },
                timeout=self.timeout,
            )
            if resp.status_code != 200:
                return None
            return resp.text
        except Exception:
            return None
