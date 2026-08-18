"""
Level 2: messy/malformed data must not break the sync.

The seed data contains 4 genuinely broken records:
  - one with no crm id at all
  - one with email = None
  - one with email = "" (empty string, a different flavor of missing)
  - one with an unparseable updated_at

A correct sync quarantines these four (with a reason) and still
successfully syncs every valid record in the same batch.
"""

from __future__ import annotations


def test_sync_does_not_crash_on_malformed_batch(client):
    resp = client.post("/sync")
    assert resp.status_code == 200, f"sync should not error out on bad records: {resp.text}"


def test_malformed_records_are_quarantined(client):
    client.post("/sync")
    quarantined = client.get("/quarantine").json()
    reasons_by_crm_id = {q["crm_id"]: q["reason"] for q in quarantined}

    assert None in reasons_by_crm_id or "" in reasons_by_crm_id or len(
        [q for q in quarantined if q["crm_id"] is None]
    ) >= 1, "the record with no crm id should be quarantined"

    assert "C-1003" in reasons_by_crm_id, "the record with email=None should be quarantined"
    assert "C-1016" in reasons_by_crm_id, "the record with email='' should be quarantined"
    assert "C-1007" in reasons_by_crm_id, "the record with an unparseable updated_at should be quarantined"

    for q in quarantined:
        assert q["reason"], "quarantine reason should be a non-empty explanation, not just a flag"


def test_valid_records_still_sync_despite_bad_ones_in_batch(client):
    client.post("/sync")
    customers = client.get("/customers").json()
    emails = {(c.get("email") or "").lower() for c in customers}

    # Priya has all required fields (deleted=True is a separate, level-5
    # concern — she should still land in `customers` for level 2's purposes).
    assert "priya.nair@acme.com" in emails
    # Bob Lee's record (C-1003) is the one that's missing email — but plenty
    # of *other* valid records are in the same page/batch and must not be
    # collateral damage.
    assert "derek.chan@beta.com" in emails
    assert "fatima.ali@gamma.com" in emails
