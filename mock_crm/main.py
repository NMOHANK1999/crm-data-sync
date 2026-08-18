"""
Mock legacy CRM.

This is the "given" system — you don't need to modify it (though nothing
stops you from reading it closely, which you should, since the messiness of
its data is the whole exercise). Run it with:

    uvicorn mock_crm.main:app --port 8001 --reload

Endpoints:
    GET  /api/contacts                 paginated list of contacts
         ?page=1&page_size=10          pagination
         ?since=<ISO8601>              only contacts updated at/after this time
    GET  /api/contacts/{crm_id}        a single contact (404 if not found)
    POST /api/_admin/reset             restore the original seed data
    POST /api/_admin/mutate/{crm_id}   patch a contact's fields and bump
                                        updated_at to now — use this to
                                        practice re-sync / update propagation
    POST /api/_admin/flaky?on=true     make ~1 in 4 requests return a 503,
                                        to practice retry handling (optional,
                                        off by default)
"""

from __future__ import annotations

import random
from datetime import datetime, timezone
from typing import Optional

from fastapi import FastAPI, HTTPException, Query
from pydantic import BaseModel

from mock_crm.seed_data import fresh_seed

app = FastAPI(title="Legacy CRM (mock)")

_STATE: dict = {
    "contacts": fresh_seed(),
    "flaky": False,
}


def _now_iso() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _maybe_flake() -> None:
    if _STATE["flaky"] and random.random() < 0.25:
        raise HTTPException(status_code=503, detail="CRM temporarily unavailable")


@app.get("/api/contacts")
def list_contacts(
    page: int = Query(1, ge=1),
    page_size: int = Query(10, ge=1, le=100),
    since: Optional[str] = Query(None, description="ISO8601 — only contacts updated at/after this time"),
):
    _maybe_flake()
    contacts = _STATE["contacts"]

    if since:
        filtered = []
        for c in contacts:
            ts = c.get("updated_at")
            if not ts:
                continue
            try:
                ts_parsed = datetime.strptime(ts, "%Y-%m-%dT%H:%M:%SZ").replace(tzinfo=timezone.utc)
                since_parsed = datetime.strptime(since, "%Y-%m-%dT%H:%M:%SZ").replace(tzinfo=timezone.utc)
            except ValueError:
                continue
            if ts_parsed >= since_parsed:
                filtered.append(c)
        contacts = filtered

    total = len(contacts)
    start = (page - 1) * page_size
    end = start + page_size
    page_items = contacts[start:end]

    return {
        "results": page_items,
        "page": page,
        "page_size": page_size,
        "total": total,
        "has_more": end < total,
    }


@app.get("/api/contacts/{crm_id}")
def get_contact(crm_id: str):
    _maybe_flake()
    for c in _STATE["contacts"]:
        if c.get("id") == crm_id:
            return c
    raise HTTPException(status_code=404, detail="not found")


@app.post("/api/_admin/reset")
def reset():
    _STATE["contacts"] = fresh_seed()
    _STATE["flaky"] = False
    return {"status": "reset"}


class MutatePayload(BaseModel):
    fields: dict


@app.post("/api/_admin/mutate/{crm_id}")
def mutate(crm_id: str, payload: MutatePayload):
    """Patch a contact by crm_id (first match). Bumps updated_at to now,
    unless payload.fields explicitly includes an updated_at (useful for
    simulating a stale/out-of-order replay with an older timestamp)."""
    for c in _STATE["contacts"]:
        if c.get("id") == crm_id:
            c.update(payload.fields)
            if "updated_at" not in payload.fields:
                c["updated_at"] = _now_iso()
            return c
    raise HTTPException(status_code=404, detail="not found")


@app.post("/api/_admin/flaky")
def set_flaky(on: bool = True):
    _STATE["flaky"] = on
    return {"flaky": _STATE["flaky"]}


@app.get("/health")
def health():
    return {"status": "ok", "contact_count": len(_STATE["contacts"])}
