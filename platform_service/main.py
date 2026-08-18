"""
Platform service.

    uvicorn platform_service.main:app --port 8000 --reload

Endpoints:
    GET  /health
    POST /sync              runs a full sync from the CRM (?since= optional)
    GET  /customers          list synced customers (implemented for you —
                              use it to eyeball your sync results)
    GET  /customers/{id}
    GET  /quarantine         list quarantined raw records
"""

from __future__ import annotations

import json
from contextlib import asynccontextmanager
from typing import Optional

from fastapi import FastAPI, HTTPException

from platform_service.db import get_connection, init_db


@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    yield


app = FastAPI(title="Platform Sync Service", lifespan=lifespan)


@app.get("/health")
def health():
    return {"status": "ok"}


@app.post("/sync")
def sync(since: Optional[str] = None):
    from platform_service.sync import run_sync  # local import: fails loudly per-request, not at boot

    try:
        report = run_sync(since=since)
    except NotImplementedError as e:
        raise HTTPException(status_code=501, detail=str(e))
    return report


def _row_to_customer(row) -> dict:
    d = dict(row)
    d["crm_ids"] = json.loads(d["crm_ids"]) if d.get("crm_ids") else []
    d["is_active"] = bool(d["is_active"]) if d["is_active"] is not None else None
    return d


@app.get("/customers")
def list_customers():
    conn = get_connection()
    try:
        rows = conn.execute("SELECT * FROM customers ORDER BY id").fetchall()
        return [_row_to_customer(r) for r in rows]
    finally:
        conn.close()


@app.get("/customers/{customer_id}")
def get_customer(customer_id: int):
    conn = get_connection()
    try:
        row = conn.execute("SELECT * FROM customers WHERE id = ?", (customer_id,)).fetchone()
        if not row:
            raise HTTPException(status_code=404, detail="not found")
        return _row_to_customer(row)
    finally:
        conn.close()


@app.get("/quarantine")
def list_quarantine():
    conn = get_connection()
    try:
        rows = conn.execute("SELECT * FROM sync_quarantine ORDER BY id").fetchall()
        out = []
        for r in rows:
            d = dict(r)
            d["raw"] = json.loads(d.pop("raw_json"))
            out.append(d)
        return out
    finally:
        conn.close()
