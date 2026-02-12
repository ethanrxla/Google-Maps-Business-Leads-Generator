"""Database layer for the leads pipeline.

Provides Supabase client access and repository functions
for candidates, verified_leads, packs, and batch_runs.
"""

from db.supabase_client import get_client

__all__ = ["get_client"]
