import requests

def fetch_html(url: str) -> str | None:
    try:
        resp = requests.get(
            url,
            timeout=10,
            headers={"User-Agent": "Mozilla/5.0 LeadgenBot"}
        )
        if resp.status_code == 200:
            return resp.text
        return None
    except Exception:
        return None
