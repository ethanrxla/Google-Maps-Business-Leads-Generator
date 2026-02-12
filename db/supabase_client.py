"""Supabase client singleton with environment validation."""

import os
from typing import Optional

from dotenv import load_dotenv

load_dotenv()

_client: Optional[object] = None


class SupabaseConfigError(Exception):
    """Raised when required Supabase environment variables are missing."""


def _validate_env() -> tuple[str, str]:
    """Validate and return (SUPABASE_URL, SUPABASE_SERVICE_KEY)."""
    url = os.getenv("SUPABASE_URL", "").strip()
    key = os.getenv("SUPABASE_SERVICE_KEY", "").strip()

    missing = []
    if not url:
        missing.append("SUPABASE_URL")
    if not key:
        missing.append("SUPABASE_SERVICE_KEY")

    if missing:
        raise SupabaseConfigError(
            f"Missing required environment variables: {', '.join(missing)}. "
            f"Add them to your .env file. See .env.example for reference."
        )

    if not url.startswith("https://"):
        raise SupabaseConfigError(
            f"SUPABASE_URL must start with https:// (got: {url[:30]}...)"
        )

    return url, key


def get_client():
    """Return a configured Supabase client (singleton).

    Raises SupabaseConfigError if SUPABASE_URL or SUPABASE_SERVICE_KEY
    are missing or invalid.
    """
    global _client
    if _client is not None:
        return _client

    url, key = _validate_env()

    from supabase import create_client

    _client = create_client(url, key)
    return _client


def reset_client() -> None:
    """Reset the singleton (useful for testing)."""
    global _client
    _client = None
