"""Canonical domain resolution with auditable outputs.

Every resolution produces a DomainResolution dataclass with:
- resolved_domain: the canonical domain (e.g., "example.com")
- resolved_url_ok: whether the URL is reachable
- resolver_method: how the domain was resolved
- resolver_notes: human-readable audit notes
- unresolved_reason: why resolution failed (if it did)

Resolver methods (deterministic taxonomy):
- "urlparse"         : standard URL parsing
- "urlparse_heuristic" : URL lacked scheme, scheme was inferred
- "redirect_follow"  : followed HTTP redirect to canonical domain
- "unresolved"       : could not resolve
"""

import re
from dataclasses import dataclass
from typing import Optional
from urllib.parse import urlparse


@dataclass
class DomainResolution:
    """Auditable result of domain resolution."""
    input_url: str
    resolved_domain: Optional[str]
    resolved_url_ok: bool
    resolver_method: str
    resolver_notes: str
    unresolved_reason: Optional[str] = None

    def to_dict(self) -> dict:
        return {
            "input_url": self.input_url,
            "resolved_domain": self.resolved_domain,
            "resolved_url_ok": self.resolved_url_ok,
            "resolver_method": self.resolver_method,
            "resolver_notes": self.resolver_notes,
            "unresolved_reason": self.unresolved_reason,
        }


# Unresolved reason taxonomy (deterministic strings)
REASON_EMPTY_INPUT = "empty_input"
REASON_NO_DOMAIN_PARSED = "no_domain_parsed"
REASON_IP_ADDRESS = "ip_address_not_domain"
REASON_LOCAL_DOMAIN = "local_or_internal_domain"
REASON_INVALID_TLD = "invalid_tld"

# Patterns
_IP_RE = re.compile(r"^\d{1,3}(\.\d{1,3}){3}$")
_LOCAL_DOMAINS = frozenset({"localhost", "127.0.0.1", "0.0.0.0"})
_MIN_TLD_LENGTH = 2


def _strip_www(domain: str) -> str:
    """Remove leading www. prefix."""
    if domain.startswith("www."):
        return domain[4:]
    return domain


def resolve_domain(url: Optional[str]) -> DomainResolution:
    """Resolve a URL to its canonical domain.

    Handles edge cases:
    - Missing scheme (adds https://)
    - www. prefix (stripped)
    - IP addresses (flagged as unresolved)
    - Local/internal domains (flagged)
    - Trailing paths/query strings (stripped)

    Does NOT make HTTP requests. For liveness checking,
    use a separate website_alive check.
    """
    if not url or not url.strip():
        return DomainResolution(
            input_url=url or "",
            resolved_domain=None,
            resolved_url_ok=False,
            resolver_method="unresolved",
            resolver_notes="Input URL is empty or whitespace",
            unresolved_reason=REASON_EMPTY_INPUT,
        )

    url_clean = url.strip()
    method = "urlparse"
    notes_parts = []

    # Add scheme if missing
    if "://" not in url_clean:
        url_clean = f"https://{url_clean}"
        method = "urlparse_heuristic"
        notes_parts.append("scheme_inferred=https")

    parsed = urlparse(url_clean)
    domain = (parsed.netloc or parsed.path.split("/")[0]).lower()

    if not domain:
        return DomainResolution(
            input_url=url,
            resolved_domain=None,
            resolved_url_ok=False,
            resolver_method="unresolved",
            resolver_notes="Could not extract domain from URL",
            unresolved_reason=REASON_NO_DOMAIN_PARSED,
        )

    # Strip port
    if ":" in domain:
        domain = domain.split(":")[0]

    # Strip www
    original_domain = domain
    domain = _strip_www(domain)
    if domain != original_domain:
        notes_parts.append("www_stripped")

    # Check for IP address
    if _IP_RE.match(domain):
        return DomainResolution(
            input_url=url,
            resolved_domain=domain,
            resolved_url_ok=False,
            resolver_method="unresolved",
            resolver_notes="Input is an IP address, not a domain name",
            unresolved_reason=REASON_IP_ADDRESS,
        )

    # Check for local/internal
    if domain in _LOCAL_DOMAINS or domain.endswith(".local"):
        return DomainResolution(
            input_url=url,
            resolved_domain=domain,
            resolved_url_ok=False,
            resolver_method="unresolved",
            resolver_notes="Domain is local/internal",
            unresolved_reason=REASON_LOCAL_DOMAIN,
        )

    # Check TLD validity
    parts = domain.split(".")
    if len(parts) < 2 or len(parts[-1]) < _MIN_TLD_LENGTH:
        return DomainResolution(
            input_url=url,
            resolved_domain=domain,
            resolved_url_ok=False,
            resolver_method="unresolved",
            resolver_notes=f"Domain has invalid TLD: {parts[-1] if parts else '(none)'}",
            unresolved_reason=REASON_INVALID_TLD,
        )

    notes = "; ".join(notes_parts) if notes_parts else "clean_parse"

    return DomainResolution(
        input_url=url,
        resolved_domain=domain,
        resolved_url_ok=True,  # structurally valid; liveness requires HTTP check
        resolver_method=method,
        resolver_notes=notes,
    )
