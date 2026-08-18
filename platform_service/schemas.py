"""
Pydantic models for the platform service's own API responses.

You are free to add fields, add validators, or introduce additional models
(e.g. a RawCrmContact model) as your implementation needs. Nothing here is
required to stay exactly as-is — this is a starting point, not a spec.
"""

from __future__ import annotations

from typing import Optional

from pydantic import BaseModel


class Customer(BaseModel):
    id: int
    crm_ids: list[str]
    full_name: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None
    company: Optional[str] = None
    is_active: Optional[bool] = None
    source_updated_at: Optional[str] = None
    created_at: str
    updated_at: str


class QuarantinedRecord(BaseModel):
    id: int
    crm_id: Optional[str] = None
    raw: dict
    reason: str
    quarantined_at: str


class SyncReport(BaseModel):
    created: int = 0
    updated: int = 0
    skipped: int = 0
    quarantined: int = 0
    total_seen: int = 0
