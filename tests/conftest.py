"""
Shared test fixtures.

Starts the mock CRM as a real HTTP server in a background process (the way
it'd actually be deployed), points the platform service at a throwaway
SQLite file, and resets both between tests so levels don't bleed into each
other.
"""

from __future__ import annotations

import multiprocessing
import os
import socket
import tempfile
import time

import httpx
import pytest
import uvicorn


def _run_crm_server(port: int):
    uvicorn.run("mock_crm.main:app", host="127.0.0.1", port=port, log_level="warning")


def _wait_for_server(url: str, timeout: float = 10.0):
    deadline = time.time() + timeout
    while time.time() < deadline:
        try:
            r = httpx.get(url, timeout=0.5, trust_env=False)
            if r.status_code == 200:
                return
        except httpx.HTTPError:
            pass
        time.sleep(0.1)
    raise RuntimeError(f"server at {url} never came up")


def _free_port() -> int:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind(("127.0.0.1", 0))
        return s.getsockname()[1]


@pytest.fixture(scope="session")
def crm_port():
    port = _free_port()
    proc = multiprocessing.Process(target=_run_crm_server, args=(port,), daemon=True)
    proc.start()
    _wait_for_server(f"http://127.0.0.1:{port}/health")
    yield port
    proc.terminate()
    proc.join(timeout=5)


@pytest.fixture(autouse=True)
def _point_sync_at_test_crm(crm_port, monkeypatch):
    """Every test gets the CRM_BASE_URL pointed at the background test
    server, and a fresh CRM state (seed data restored)."""
    import platform_service.sync as sync_module

    monkeypatch.setattr(sync_module, "CRM_BASE_URL", f"http://127.0.0.1:{crm_port}")
    httpx.post(f"http://127.0.0.1:{crm_port}/api/_admin/reset", timeout=5.0, trust_env=False)
    yield


@pytest.fixture()
def platform_db(tmp_path, monkeypatch):
    """Fresh SQLite file per test."""
    db_file = tmp_path / "platform_test.db"
    monkeypatch.setenv("PLATFORM_DB_PATH", str(db_file))

    from platform_service.db import init_db

    init_db()
    yield str(db_file)


@pytest.fixture()
def client(platform_db):
    from fastapi.testclient import TestClient
    from platform_service.main import app

    with TestClient(app) as c:
        yield c


@pytest.fixture()
def crm_client(crm_port):
    return httpx.Client(base_url=f"http://127.0.0.1:{crm_port}", timeout=5.0, trust_env=False)
