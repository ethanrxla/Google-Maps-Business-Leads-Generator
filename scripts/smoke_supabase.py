#!/usr/bin/env python3
"""Smoke test for Supabase connectivity and candidates CRUD.

Usage:
    python scripts/smoke_supabase.py

Prerequisites:
    1. Supabase project created with schema from db/migrations/001_core_tables.sql
    2. SUPABASE_URL and SUPABASE_SERVICE_KEY set in .env
    3. `pip install supabase python-dotenv`

Exit codes:
    0 = PASS (all checks succeeded)
    1 = FAIL (with explanation)
"""

import sys
import uuid
from pathlib import Path

# Ensure project root is on sys.path so `db` package is importable
PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))


def main() -> int:
    print("=" * 60)
    print("Supabase Smoke Test")
    print("=" * 60)

    # Step 1: Environment validation
    print("\n[1/5] Checking environment variables...")
    try:
        from db.supabase_client import get_client, SupabaseConfigError
    except ImportError as e:
        print(f"FAIL: Cannot import db package: {e}")
        print("  -> Make sure you're running from the project root")
        return 1

    try:
        client = get_client()
        print("  OK: Supabase client created")
    except SupabaseConfigError as e:
        print(f"FAIL: {e}")
        return 1
    except Exception as e:
        print(f"FAIL: Unexpected error creating client: {e}")
        return 1

    # Step 2: Create a batch_run (needed as FK for candidate)
    print("\n[2/5] Creating test batch_run...")
    test_batch_id = None
    try:
        from db.repositories import create_batch_run
        batch = create_batch_run(
            batch_type="city_sweep",
            config={"test": True, "smoke_test": True},
        )
        test_batch_id = batch["id"]
        print(f"  OK: batch_run created: {test_batch_id}")
    except Exception as e:
        print(f"FAIL: Could not create batch_run: {e}")
        print("  -> Have you run db/migrations/001_core_tables.sql in Supabase?")
        return 1

    # Step 3: Insert a test candidate
    print("\n[3/5] Inserting test candidate...")
    test_candidate_id = None
    try:
        from db.repositories import insert_candidate
        candidate_row = insert_candidate({
            "name": "Smoke Test Business",
            "name_normalized": "smoke test business",
            "source": "manual",
            "city": "Test City",
            "city_normalized": "testcity",
            "state": "FL",
            "country": "US",
            "email_raw": "test@smoketest.example.com",
            "email_source": "manual",
            "website": "https://smoketest.example.com",
            "status": "new",
            "collection_batch_id": test_batch_id,
            "has_website": True,
            "needs_website": False,
            "needs_redesign": True,
            "needs_chatbot": True,
            "needs_ai_integration": False,
        })
        test_candidate_id = candidate_row["id"]
        print(f"  OK: candidate created: {test_candidate_id}")
    except Exception as e:
        print(f"FAIL: Could not insert candidate: {e}")
        return 1

    # Step 4: Read back and verify
    print("\n[4/5] Reading back candidate...")
    try:
        from db.repositories import get_candidate
        fetched = get_candidate(test_candidate_id)
        if fetched is None:
            print(f"FAIL: Candidate {test_candidate_id} not found after insert")
            return 1

        checks = [
            ("name", fetched.get("name"), "Smoke Test Business"),
            ("source", fetched.get("source"), "manual"),
            ("status", fetched.get("status"), "new"),
            ("city", fetched.get("city"), "Test City"),
            ("email_raw", fetched.get("email_raw"), "test@smoketest.example.com"),
        ]
        all_ok = True
        for field_name, actual, expected in checks:
            if actual == expected:
                print(f"  OK: {field_name} = {actual!r}")
            else:
                print(f"  MISMATCH: {field_name}: expected {expected!r}, got {actual!r}")
                all_ok = False

        if not all_ok:
            print("FAIL: Field verification failed")
            return 1

    except Exception as e:
        print(f"FAIL: Could not read candidate: {e}")
        return 1

    # Step 5: Clean up test data
    print("\n[5/5] Cleaning up test data...")
    try:
        from db.repositories import delete_candidate
        deleted = delete_candidate(test_candidate_id)
        print(f"  OK: candidate deleted: {deleted}")

        # Also clean up the batch_run
        client.table("batch_runs").delete().eq("id", test_batch_id).execute()
        print(f"  OK: batch_run deleted")
    except Exception as e:
        print(f"  WARN: Cleanup failed (not critical): {e}")

    # Final result
    print("\n" + "=" * 60)
    print("PASS: All checks succeeded")
    print("=" * 60)
    return 0


if __name__ == "__main__":
    sys.exit(main())
