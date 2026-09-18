"""FastAPI adapter over the engine. Everything requires the per-launch bearer token."""

import hmac
import sqlite3

from fastapi import Depends, FastAPI, Header, HTTPException
from fastapi.middleware.cors import CORSMiddleware

from kataki import __version__


def create_app(conn: sqlite3.Connection, token: str) -> FastAPI:
    def require_token(authorization: str = Header("")):
        if not hmac.compare_digest(authorization.encode(), f"Bearer {token}".encode()):
            raise HTTPException(401, "missing or invalid token")

    app = FastAPI(
        title="Kataki RPAI engine", version=__version__, dependencies=[Depends(require_token)]
    )
    # Any origin is fine: auth is a bearer token, not a cookie, so a foreign page has
    # nothing to ride on.
    app.add_middleware(
        CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"]
    )

    @app.get("/health")
    def health():
        schema = conn.execute("PRAGMA user_version").fetchone()[0]
        return {"status": "ok", "version": __version__, "schema": schema}

    return app
