"""
Level 4: cross-id dedup and stale-write protection.

Two problems, both about correctness under conflicting data:

  1. C-1001 and C-1005 are the SAME real person (same normalized email,
     different crm_id). They should collapse into one customer row, with
     both source ids retained.

  2. A record with an older updated_at than what's already stored for a
     crm_id must not clobber the newer data — "last write wins" should
     mean latest by updated_at, not latest by arrival order.
"""

from __future__ import annotations


def _find_by_email(customers: list[dict], email: str) -> dict | None:
    for c in customers:
        if (c.get("email") or "").lower() == email.lower():
            return c
    return None


def test_same_person_different_crm_ids_merge_into_one_customer(client):
    client.post("/sync")
    customers = client.get("/customers").json()

    matches = [c for c in customers if (c.get("email") or "").lower() == "john.smith@acme.com"]
    assert len(matches) == 1, (
        f"C-1001 and C-1005 share an email and should merge into one customer, "
        f"found {len(matches)} rows instead"
    )

    merged = matches[0]
    assert set(merged["crm_ids"]) >= {"C-1001", "C-1005"}, (
        f"merged row should retain both source crm_ids, got {merged['crm_ids']}"
    )

    # The most recent underlying CRM update was C-1005 at 2026-06-05T08:00:00Z
    # — newer than both C-1001's original (06-01) and the stale duplicate
    # (2026-01-01). The row should reflect that, not an earlier snapshot.
    assert merged.get("source_updated_at", "") >= "2026-06-05", (
        f"expected the merged row's source_updated_at to reflect the newest "
        f"contributing record, got {merged.get('source_updated_at')!r}"
    )


def test_stale_update_does_not_overwrite_newer_data(client, crm_client):
    client.post("/sync")
    customers = client.get("/customers").json()
    fatima_before = _find_by_email(customers, "fatima.ali@gamma.com")
    assert fatima_before is not None
    original_company = fatima_before["company"]

    # Simulate a stale/out-of-order replay: an update with an OLDER
    # updated_at than what's already been synced for this crm_id.
    r = crm_client.post(
        "/api/_admin/mutate/C-1012",
        json={"fields": {"company": "Should Not Win", "updated_at": "2020-01-01T00:00:00Z"}},
    )
    assert r.status_code == 200

    client.post("/sync")
    customers_after = client.get("/customers").json()
    fatima_after = _find_by_email(customers_after, "fatima.ali@gamma.com")

    assert fatima_after["company"] == original_company, (
        "a record with an older updated_at than what's already stored should not "
        f"overwrite it (company became {fatima_after['company']!r})"
    )
