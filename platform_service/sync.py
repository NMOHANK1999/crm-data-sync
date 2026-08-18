"""
Sync logic: pull contacts from the legacy CRM and land them correctly in the
platform's `customers` table.

fetch_all_contacts() is fully implemented for you (pagination is handled).
Everything else is a stub for you to build, level by level. Read
tests/test_level*.py for exactly what's being graded at each level — don't
guess, the tests are the spec.

LEVELS
------
Level 1 (test_level1_basic_sync.py):
    Implement normalize_contact() for the *clean* records and wire up
    run_sync() to insert them into `customers`. Malformed records can
    crash, be dropped, or be quarantined for now — level 2 is where that
    gets formalized.

Level 2 (test_level2_messy_data.py):
    Sync must not crash on a batch that contains malformed records
    (missing id, missing/empty email, unparseable updated_at). Invalid
    records should be written to `sync_quarantine` with a reason, and
    valid records in the same batch should still sync successfully.

Level 3 (test_level3_idempotent_upsert.py):
    Running /sync twice must not create duplicate customers. Running it
    again after a CRM record changes (see POST /api/_admin/mutate) must
    update the existing row rather than insert a new one.

Level 4 (test_level4_dedup_conflict.py):
    Two CRM records with different crm_ids but the same normalized email
    represent the same person and should collapse into one customer row
    (crm_ids should accumulate both source ids). Separately: a stale
    record (older updated_at) for a crm_id that's already been synced with
    a newer updated_at must not overwrite the newer data.

Level 5 (test_level5_open_ended.py):
    Open-ended — no single correct answer, tests check for reasonable
    behavior, not an exact implementation. Ideas: incremental sync using
    the `since` cursor instead of a full pull every time; handling soft
    deletes (the `deleted` flag) by marking customers inactive rather than
    leaving stale active rows; surfacing a meaningful SyncReport.
"""

from __future__ import annotations

import json
from datetime import datetime, timezone
from typing import Optional

import httpx

from platform_service.db import get_connection

CRM_BASE_URL = "http://localhost:8001"


# ---------------------------------------------------------------------------
# GIVEN — fetch layer. You shouldn't need to change this, but read it: it's
# what your normalize/upsert functions will receive.
# ---------------------------------------------------------------------------

def fetch_all_contacts(since: Optional[str] = None, page_size: int = 10) -> list[dict]:
    """Pull every contact from the mock CRM, following pagination.

    Returns the raw, messy dicts exactly as the CRM sends them — no
    normalization happens here.
    """
    contacts: list[dict] = []
    page = 1
    with httpx.Client(base_url=CRM_BASE_URL, timeout=5.0, trust_env=False) as client:
        while True:
            params = {"page": page, "page_size": page_size}
            if since:
                params["since"] = since
            resp = client.get("/api/contacts", params=params)
            resp.raise_for_status()
            data = resp.json()
            contacts.extend(data["results"])
            if not data["has_more"]:
                break
            page += 1
    return contacts


# ---------------------------------------------------------------------------
# TODO — Level 1 & 2
# ---------------------------------------------------------------------------

def normalize_contact(raw: dict) -> dict:
    """Turn a raw CRM contact dict into a normalized shape ready for
    upsert_customer().

    Must handle (see levels 1 & 2):
      - first_name/last_name OR full_name -> a single full_name
      - status (string, various casings) OR is_active (bool) -> a single
        boolean is_active
      - email: trim + lowercase; treat "" the same as missing
      - phone: normalize formatting (your call on the target format —
        document your choice in DECISIONS.md)
      - updated_at: parse to a comparable form; raise/flag if unparseable

    Raise ValueError(reason) for anything that should be quarantined
    (e.g. missing crm id, missing email, unparseable updated_at). Callers
    are expected to catch ValueError and route to quarantine.
    """
    raise NotImplementedError("Level 1/2: implement normalize_contact")


# ---------------------------------------------------------------------------
# TODO — Level 3
# ---------------------------------------------------------------------------

def upsert_customer(conn, normalized: dict) -> str:
    """Insert or update a customer row for this normalized contact.

    Must be idempotent: calling this twice with the same input should not
    create a second row. Should update in place when the crm_id already
    exists on a row, and should not regress source_updated_at backwards in
    time (see level 4 for the cross-id version of this problem).

    Return "created" or "updated".
    """
    raise NotImplementedError("Level 3: implement upsert_customer")


# ---------------------------------------------------------------------------
# TODO — Level 4
# ---------------------------------------------------------------------------

def find_existing_customer(conn, normalized: dict):
    """Find a customer row that this normalized contact should merge into,
    even if it arrived under a different crm_id — e.g. by matching on
    normalized email. Return the row, or None if this looks like a new
    customer.
    """
    raise NotImplementedError("Level 4: implement find_existing_customer")


# ---------------------------------------------------------------------------
# TODO — Level 5 (open-ended)
# ---------------------------------------------------------------------------

def run_sync(since: Optional[str] = None) -> dict:
    """Orchestrate a full sync: fetch, normalize, upsert, quarantine bad
    records, and return a report.

    A basic version is wired up for you below — it fetches everything and
    calls your (currently unimplemented) normalize_contact/upsert_customer.
    Feel free to rewrite this entirely once you get to level 5 (e.g. to
    support incremental sync via `since`, or soft-delete handling).
    """
    conn = get_connection()
    report = {"created": 0, "updated": 0, "skipped": 0, "quarantined": 0, "total_seen": 0}
    try:
        raw_contacts = fetch_all_contacts(since=since)
        report["total_seen"] = len(raw_contacts)

        for raw in raw_contacts:
            try:
                normalized = normalize_contact(raw)
            except ValueError as e:
                quarantine(conn, raw, reason=str(e))
                report["quarantined"] += 1
                continue

            result = upsert_customer(conn, normalized)
            if result == "created":
                report["created"] += 1
            elif result == "updated":
                report["updated"] += 1
            else:
                report["skipped"] += 1

        conn.commit()
    finally:
        conn.close()

    return report


# ---------------------------------------------------------------------------
# GIVEN — quarantine helper
# ---------------------------------------------------------------------------

def quarantine(conn, raw: dict, reason: str) -> None:
    conn.execute(
        "INSERT INTO sync_quarantine (crm_id, raw_json, reason, quarantined_at) VALUES (?, ?, ?, ?)",
        (raw.get("id"), json.dumps(raw), reason, datetime.now(timezone.utc).isoformat()),
    )
