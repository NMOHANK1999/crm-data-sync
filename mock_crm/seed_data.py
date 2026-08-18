"""
Seed data for the mock legacy CRM.

This data is DELIBERATELY messy, in ways that mirror real legacy CRM exports:
  - Schema drift: some records use first_name/last_name, some use a single
    full_name, some use is_active (bool) instead of status (string).
  - Missing required fields: some records have no id, no email.
  - Formatting inconsistency: emails with mixed case / whitespace, phone
    numbers in several formats.
  - Duplicates: the same real person appears under two different crm ids.
  - Out-of-order updates: the same crm id appears twice with different
    updated_at timestamps, in an order that doesn't match update recency.
  - Soft deletes: a `deleted` flag that isn't present on every record.
  - Bad values: a non-parseable updated_at string.

Do not "clean this up" — the messiness is the point. Your sync logic is
what's supposed to make sense of it.
"""

from __future__ import annotations

import copy

SEED_CONTACTS: list[dict] = [
    {
        "id": "C-1001",
        "first_name": "John",
        "last_name": "Smith",
        "email": "John.Smith@Acme.com",
        "phone": "555-123-4567",
        "company": "Acme Corp",
        "status": "active",
        "updated_at": "2026-06-01T10:00:00Z",
    },
    {
        "id": "C-1002",
        # schema drift: full_name instead of first/last
        "full_name": "Jane Doe",
        "email": "jane.doe@acme.com",
        "phone": "(555) 234-5678",
        "company": "Acme Corp",
        "status": "active",
        "updated_at": "2026-06-02T09:00:00Z",
    },
    {
        "id": "C-1003",
        "first_name": "Bob",
        "last_name": "Lee",
        "email": None,  # missing required field
        "phone": "5553456789",
        "company": "Beta LLC",
        "status": "inactive",
        "updated_at": "2026-06-03T11:00:00Z",
    },
    {
        "id": "C-1004",
        "first_name": "Alice",
        "last_name": "Wong",
        "email": "ALICE.WONG@acme.com",
        "phone": None,
        "company": "Acme Corp",
        # schema drift: is_active bool instead of status string
        "is_active": True,
        "updated_at": "2026-06-04T12:00:00Z",
    },
    {
        # same real person as C-1001 (same normalized email), different id,
        # NEWER updated_at, slightly different phone formatting
        "id": "C-1005",
        "first_name": "John",
        "last_name": "Smith",
        "email": "john.smith@acme.com",
        "phone": "555.123.4567",
        "company": "Acme Corp",
        "status": "Active",
        "updated_at": "2026-06-05T08:00:00Z",
    },
    {
        # malformed: no id at all
        "id": None,
        "first_name": "No",
        "last_name": "Id",
        "email": "no.id@acme.com",
        "phone": "5551110000",
        "company": "Gamma Inc",
        "status": "active",
        "updated_at": "2026-06-06T10:00:00Z",
    },
    {
        "id": "C-1007",
        "first_name": "Carlos",
        "last_name": "Ruiz",
        "email": "carlos@acme.com",
        "phone": "not-a-phone-number",
        "company": "Gamma Inc",
        "status": "active",
        "updated_at": "not-a-real-date",  # malformed timestamp
    },
    {
        "id": "C-1008",
        "first_name": "Priya",
        "last_name": "Nair",
        "email": "priya.nair@acme.com",
        "phone": "5559998888",
        "company": "Beta LLC",
        "status": "active",
        "updated_at": "2026-05-01T10:00:00Z",
        "deleted": True,  # soft delete
    },
    {
        # duplicate of C-1001's crm_id, but a STALE snapshot (older
        # updated_at) with a bogus phone number. Simulates a stale replay /
        # out-of-order delivery within the same page.
        "id": "C-1001",
        "first_name": "John",
        "last_name": "Smith",
        "email": "john.smith@acme.com",
        "phone": "000-000-0000",
        "company": "Acme Corp",
        "status": "active",
        "updated_at": "2026-01-01T00:00:00Z",
    },
    {
        "id": "C-1010",
        "first_name": "  Maria  ",
        "last_name": "Garcia ",
        "email": " maria.garcia@ACME.com ",
        "phone": "+1 555 111 2222",
        "company": "Acme Corp",
        "status": "ACTIVE",
        "updated_at": "2026-06-10T10:00:00Z",
    },
    {
        "id": "C-1011",
        "first_name": "Derek",
        "last_name": "Chan",
        "email": "derek.chan@beta.com",
        "phone": "555-777-1212",
        "company": "Beta LLC",
        "status": "inactive",
        "updated_at": "2026-06-07T10:00:00Z",
    },
    {
        "id": "C-1012",
        "first_name": "Fatima",
        "last_name": "Ali",
        "email": "fatima.ali@gamma.com",
        "phone": "555-222-3333",
        "company": "Gamma Inc",
        "status": "active",
        "updated_at": "2026-06-08T10:00:00Z",
    },
    {
        "id": "C-1013",
        "full_name": "Tom O'Brien",
        "email": "tom.obrien@gamma.com",
        "phone": "555-444-5555",
        "company": "Gamma Inc",
        "is_active": False,
        "updated_at": "2026-06-09T10:00:00Z",
    },
    {
        "id": "C-1014",
        "first_name": "Grace",
        "last_name": "Kim",
        "email": "grace.kim@beta.com",
        "phone": "555-666-7777",
        "company": "Beta LLC",
        "status": "active",
        "updated_at": "2026-06-11T10:00:00Z",
    },
    {
        "id": "C-1015",
        "first_name": "Hassan",
        "last_name": "Malik",
        "email": "hassan.malik@acme.com",
        "phone": "555-888-9999",
        "company": "Acme Corp",
        "status": "active",
        "updated_at": "2026-06-12T10:00:00Z",
    },
    {
        "id": "C-1016",
        "first_name": "Ingrid",
        "last_name": "Olsen",
        "email": "",  # empty string, not null — a different flavor of "missing"
        "phone": "555-101-0101",
        "company": "Beta LLC",
        "status": "active",
        "updated_at": "2026-06-13T10:00:00Z",
    },
    {
        "id": "C-1017",
        "first_name": "Kenji",
        "last_name": "Sato",
        "email": "kenji.sato@gamma.com",
        "phone": "555-121-2121",
        "company": "Gamma Inc",
        "status": "active",
        "updated_at": "2026-06-14T10:00:00Z",
    },
    {
        "id": "C-1018",
        "first_name": "Lena",
        "last_name": "Petrova",
        "email": "lena.petrova@acme.com",
        "phone": "555-131-3131",
        "company": "Acme Corp",
        "status": "active",
        "updated_at": "2026-06-15T10:00:00Z",
    },
    {
        "id": "C-1019",
        "first_name": "Miguel",
        "last_name": "Santos",
        "email": "miguel.santos@beta.com",
        "phone": "555-141-4141",
        "company": "Beta LLC",
        "status": "inactive",
        "updated_at": "2026-06-16T10:00:00Z",
    },
    {
        "id": "C-1020",
        "first_name": "Nadia",
        "last_name": "Hussein",
        "email": "nadia.hussein@gamma.com",
        "phone": "555-151-5151",
        "company": "Gamma Inc",
        "status": "active",
        "updated_at": "2026-06-17T10:00:00Z",
    },
]


def fresh_seed() -> list[dict]:
    """Return a deep copy so mutations during a test/practice session don't
    leak between server restarts within the same process."""
    return copy.deepcopy(SEED_CONTACTS)
