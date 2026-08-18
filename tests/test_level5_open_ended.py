"""
Level 5: open-ended.

There's no single correct implementation here — these tests check for
reasonable behavior, not an exact spec. Two ideas the seed data supports:

  1. Soft deletes: C-1008 (Priya Nair) has `"deleted": true` in the CRM.
     A customer record that's been deleted upstream probably shouldn't
     still look like an active customer on the platform side.

  2. Meaningful sync reporting / incremental sync: the `since` param and
     the `sync_runs` table (see db.py) are there if you want to build
     real incremental sync instead of a full pull every time. This is
     intentionally not required — full-pull-every-time is a legitimate
     answer for the time available, as long as you can defend the
     tradeoff in the walkthrough.

Treat failures here as prompts to think about, not a checklist to satisfy
mechanically.
"""

from __future__ import annotations


def test_soft_deleted_record_is_not_left_looking_active(client):
    client.post("/sync")
    customers = client.get("/customers").json()
    priya = next(
        (c for c in customers if (c.get("email") or "").lower() == "priya.nair@acme.com"),
        None,
    )
    if priya is None:
        # Dropping deleted records from `customers` entirely is a
        # defensible choice.
        return
    assert priya["is_active"] is False, (
        "Priya's CRM record has deleted=true — if she's still synced, she "
        "should at least not read as an active customer"
    )


def test_sync_report_has_sane_shape(client):
    resp = client.post("/sync")
    report = resp.json()
    for key in ("created", "updated", "skipped", "quarantined", "total_seen"):
        assert key in report, f"sync report is missing '{key}'"
        assert isinstance(report[key], int) and report[key] >= 0

    accounted_for = report["created"] + report["updated"] + report["skipped"] + report["quarantined"]
    assert accounted_for <= report["total_seen"], (
        "created+updated+skipped+quarantined shouldn't exceed the number of "
        "raw records seen"
    )
