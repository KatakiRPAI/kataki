import json
import os
import subprocess
import sys
import time

import httpx2
from fastapi.testclient import TestClient

from kataki import db
from kataki.server import create_app

TOKEN = "t0k"
AUTH = {"Authorization": f"Bearer {TOKEN}"}


def test_health_rejects_missing_or_wrong_token(conn):
    client = TestClient(create_app(conn, TOKEN))
    assert client.get("/health").status_code == 401
    assert client.get("/health", headers={"Authorization": "Bearer nope"}).status_code == 401


def test_health_reports_ok_with_token(conn):
    body = TestClient(create_app(conn, TOKEN)).get("/health", headers=AUTH).json()
    assert body["status"] == "ok"
    assert body["schema"] == db.SCHEMA_VERSION


def test_browser_preflight_passes_without_token(conn):
    # the renderer (another origin) sends OPTIONS before any authorised request
    r = TestClient(create_app(conn, TOKEN)).options(
        "/health",
        headers={
            "Origin": "http://localhost:5173",
            "Access-Control-Request-Method": "GET",
            "Access-Control-Request-Headers": "authorization",
        },
    )
    assert r.status_code == 200
    assert r.headers["access-control-allow-origin"] == "*"


def test_serve_announces_port_then_exits_when_parent_closes_stdin(tmp_path):
    with subprocess.Popen(
        [sys.executable, "-m", "kataki", "serve", "--db", str(tmp_path / "l.db"), "--parent-watch"],
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        env={**os.environ, "KATAKI_TOKEN": TOKEN},
        text=True,
    ) as proc:
        try:
            hello = json.loads(proc.stdout.readline())
            assert "token" not in hello  # a token supplied by the parent is never echoed
            url = f"http://127.0.0.1:{hello['port']}/health"
            for _ in range(50):
                try:
                    assert httpx2.get(url, headers=AUTH, timeout=2).status_code == 200
                    break
                except httpx2.TransportError:
                    time.sleep(0.1)
            else:
                raise AssertionError("engine never answered /health")

            proc.stdin.close()
            assert proc.wait(timeout=10) == 0
        finally:
            proc.kill()
