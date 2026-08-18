"""
Level 3: idempotent upserts.

Running sync repeatedly with no CRM changes must not grow the customer
table. And when a CRM record actually changes, a re-sync must update the
existing row in place rather than insert a new one.

Note: the seed data contains an intentional duplicate crm_id (C-1001
appears twice, once stale) specifically so that even a *single* sync run
already exercises "don't insert twice for the same crm_id." Cross-id
dedup (same person, different crm_id) is level 4, not tested here.
"""

from __future__ import annotations


def test_repeated_sync_does_not_grow_customer_count(client):
    r1 = client.post("/sync")
    assert r1.status_code == 200, f"sync should succeed: {r1.text}"
    count_1 = len(client.get("/customers").json())
    assert count_1 > 0, "sync should have created at least some customers"

    client.post("/sync")
    count_2 = len(client.get("/customers").json())

    assert count_2 == count_1, (
        f"re-running /sync with no CRM changes should not create new rows "
        f"(got {count_1} customers after run 1, {count_2} after run 2)"
    )


def test_updated_crm_record_updates_existing_row_not_a_new_one(client, crm_client):
    client.post("/sync")
    count_before = len(client.get("/customers").json())

    # Simulate the CRM record changing between syncs.
    r = crm_client.post(
        "/api/_admin/mutate/C-1012",
        json={"fields": {"company": "Fatima Consulting LLC"}},
    )
    assert r.status_code == 200

    client.post("/sync")
    customers_after = client.get("/customers").json()
    count_after = len(customers_after)

    assert count_after == count_before, (
        "an update to an existing crm_id should update in place, not add a row "
        f"(count went from {count_before} to {count_after})"
    )

    fatima = next(
        (c for c in customers_after if (c.get("email") or "").lower() == "fatima.ali@gamma.com"),
        None,
    )
    assert fatima is not None
    assert fatima["company"] == "Fatima Consulting LLC", "the update should be reflected"
