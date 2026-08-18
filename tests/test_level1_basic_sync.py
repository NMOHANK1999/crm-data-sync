"""
Level 1: basic sync.

Get a full sync working for well-formed-ish records: fetch from the CRM,
normalize into the platform's shape, write to `customers`. Schema drift
(full_name vs first/last, is_active vs status) and light formatting cleanup
(whitespace/case) are in scope here — outright broken/missing data is
level 2's problem, not level 1's.
"""

from __future__ import annotations


def _find_by_email(customers: list[dict], email: str) -> dict | None:
    for c in customers:
        if (c.get("email") or "").lower() == email.lower():
            return c
    return None


def test_sync_endpoint_succeeds(client):
    resp = client.post("/sync")
    assert resp.status_code == 200, (
        f"expected /sync to succeed once normalize_contact/upsert_customer "
        f"are implemented, got {resp.status_code}: {resp.text}"
    )


def test_full_name_handles_schema_drift(client):
    """C-1002 only has full_name (no first_name/last_name) — a common
    legacy-CRM schema drift."""
    client.post("/sync")
    customers = client.get("/customers").json()
    jane = _find_by_email(customers, "jane.doe@acme.com")
    assert jane is not None, "Jane Doe (full_name-only record) should have synced"
    assert jane["full_name"] == "Jane Doe"


def test_is_active_handles_status_and_boolean_drift(client):
    """Some records use status: 'active'/'inactive' (any casing), others
    use is_active: true/false directly. Both should normalize to the same
    boolean field."""
    client.post("/sync")
    customers = client.get("/customers").json()

    alice = _find_by_email(customers, "alice.wong@acme.com")  # is_active: True
    assert alice is not None
    assert alice["is_active"] is True

    tom = _find_by_email(customers, "tom.obrien@gamma.com")  # is_active: False
    assert tom is not None
    assert tom["is_active"] is False

    derek = _find_by_email(customers, "derek.chan@beta.com")  # status: "inactive"
    assert derek is not None
    assert derek["is_active"] is False


def test_email_and_name_are_normalized(client):
    """C-1010 has leading/trailing whitespace and inconsistent casing on
    name and email."""
    client.post("/sync")
    customers = client.get("/customers").json()
    maria = _find_by_email(customers, "maria.garcia@acme.com")
    assert maria is not None, "email should be trimmed + lowercased for matching"
    assert maria["full_name"].strip() == "Maria Garcia"
    assert maria["is_active"] is True  # status was "ACTIVE"
