"""Cloud save: this computer's library, kept on its owner's Kataki online account.

The desktop links itself to an account once (a code the person approves on the website) and
keeps the token that comes back in the OS keychain. A snapshot is the library's own `.kataki`.
Uploading says which snapshot this library was last in step with; if the cloud has moved on, the
gateway refuses and the person chooses. Downloading never touches the open library: the copy
lands beside the backups and is swapped in at the next start, where what was there is backed up
first (`backups.apply_pending`). docs/specs/2026-10-02-kataki-online.md §8.
"""

import contextlib
import json
import os
import platform
import sqlite3
import tempfile
import zipfile
from datetime import datetime
from pathlib import Path

import httpx2
import keyring
import keyring.errors

from kataki import archive, backups, profile

SERVICE = "kataki-cloud"  # the keychain entry; the account name in it is the service's address
TRANSPORT: httpx2.AsyncBaseTransport | None = None  # tests script the gateway here


def origin() -> str | None:
    """Where Kataki online is (`KATAKI_ONLINE`); None: this build has no cloud to save to."""
    said = (os.environ.get("KATAKI_ONLINE") or "").rstrip("/")
    return said or None


Unreachable = httpx2.HTTPError  # the service could not be reached, or answered with an error


class Unlinked(Exception):
    """This computer is not linked to an account (or was unlinked from the website)."""


class Cloud:
    def __init__(self, conn: sqlite3.Connection, db_path: Path, at: str):
        self.conn, self.db_path, self.at = conn, db_path, at
        self.state = db_path.parent / "cloud.json"  # beside the library, not in it: a restore
        self._secret: str | None = None  # must not bring another computer's bookkeeping with it

    # --- what this computer remembers -------------------------------------------------------

    def token(self) -> str | None:
        with contextlib.suppress(keyring.errors.KeyringError):
            return keyring.get_password(SERVICE, self.at)
        return None

    def base(self) -> int:
        """The snapshot this library was last in step with (0: none)."""
        try:
            kept = json.loads(self.state.read_text("utf8"))
            return int(kept["base"]) if kept.get("origin") == self.at else 0
        except (OSError, ValueError, KeyError, TypeError):
            return 0

    def _in_step_with(self, revision: int) -> None:
        self.state.write_text(json.dumps({"origin": self.at, "base": revision}), "utf8")

    def holds(self) -> dict:
        got = profile.stats(self.conn)
        plots = self.conn.execute("SELECT count(*) FROM lib_items WHERE kind='scenario'")
        return {
            "stories": got["stories"],
            "characters": got["characters"],
            "places": got["places"],
            "plots": plots.fetchone()[0],
        }

    def _http(self, linked: bool = True) -> httpx2.AsyncClient:
        headers = {}
        if linked:
            if not (token := self.token()):
                raise Unlinked
            headers["Authorization"] = f"Bearer {token}"
        return httpx2.AsyncClient(
            base_url=self.at, headers=headers, timeout=60.0, transport=TRANSPORT
        )

    def _unlinked(self) -> None:
        with contextlib.suppress(keyring.errors.KeyringError):
            keyring.delete_password(SERVICE, self.at)

    # --- linking ----------------------------------------------------------------------------

    async def connect(self) -> dict:
        """Ask to be linked: the address to open and the code the person will see there."""
        async with self._http(linked=False) as http:
            r = await http.post("/api/device/start", json={"name": platform.node() or "Desktop"})
            r.raise_for_status()
        made = r.json()
        self._secret = made["secret"]
        return {"url": made["url"], "code": made["code"]}

    async def poll(self) -> str:
        """`linked`, `waiting`, or `expired` (ask again)."""
        if not self._secret:
            return "expired"
        async with self._http(linked=False) as http:
            r = await http.post("/api/device/poll", json={"secret": self._secret})
        if r.status_code == 202:
            return "waiting"
        self._secret = None
        if r.status_code != 200:
            return "expired"
        keyring.set_password(SERVICE, self.at, r.json()["token"])
        return "linked"

    async def disconnect(self) -> None:
        with contextlib.suppress(Unlinked, httpx2.HTTPError):
            async with self._http() as http:
                await http.delete("/api/cloud/device")
        self._unlinked()

    # --- the snapshot -----------------------------------------------------------------------

    async def status(self) -> dict:
        said = {"available": True, "connected": False, "base": self.base(), "local": self.holds()}
        if not self.token():
            return said
        try:
            async with self._http() as http:
                r = await http.get("/api/cloud")
        except httpx2.HTTPError:
            return said | {
                "connected": True,
                "offline": True,
            }  # linked; the service is not answering
        if r.status_code == 401:  # unlinked from the website: forget the token
            self._unlinked()
            return said
        r.raise_for_status()
        return said | {"connected": True, **r.json()}

    async def upload(self, force: bool = False) -> dict:
        """Send this library. `{"snapshot"}` when it went; `{"conflict": snapshot}` when the
        cloud holds something this library was not built on; `{"too_big": bytes}` past the size
        limit; `{"needs_credit": {over, free}}` past the free limit with no credit left."""
        with tempfile.TemporaryDirectory(prefix="kataki-") as tmp:
            made = Path(tmp) / "library.kataki"
            archive.dump(self.conn, made)
            params = {"base": self.base(), "holds": json.dumps(self.holds())}
            if force:
                params["force"] = "1"
            async with self._http() as http:
                # ponytail: read whole into memory for the request; stream it if libraries grow
                r = await http.put("/api/cloud", params=params, content=made.read_bytes())
        if r.status_code == 401:
            self._unlinked()
            raise Unlinked
        if r.status_code == 409:
            return {"conflict": r.json()["snapshot"]}
        if r.status_code == 413:
            return {"too_big": r.json().get("maxBytes")}
        if r.status_code == 402:  # past the free limit, with no credit to keep it
            said = r.json()
            return {"needs_credit": {"over": said.get("over", []), "free": said.get("free", {})}}
        r.raise_for_status()
        snapshot = r.json()["snapshot"]
        self._in_step_with(snapshot["revision"])
        return {"snapshot": snapshot}

    async def download(self) -> dict:
        """Bring the cloud's snapshot down. It replaces this library at the next start, and what
        is here now is backed up first. Raises `archive.BadArchive` if it is not a library."""
        folder = backups.folder(self.db_path)
        folder.mkdir(parents=True, exist_ok=True)
        with tempfile.TemporaryDirectory(prefix="kataki-") as tmp:
            got = Path(tmp) / "library.kataki"
            async with self._http() as http, http.stream("GET", "/api/cloud/download") as r:
                if r.status_code == 401:
                    self._unlinked()
                    raise Unlinked
                if r.status_code == 404:
                    return {"nothing": True}
                r.raise_for_status()
                revision = int(r.headers["x-kataki-revision"])
                with open(got, "wb") as w:
                    async for chunk in r.aiter_bytes():
                        w.write(chunk)
            name = f"library-{datetime.now().strftime('%Y%m%d-%H%M%S')}-from-cloud.db"
            try:
                with zipfile.ZipFile(got) as z:
                    archive._manifest(z)  # a .kataki this Kataki can read, or BadArchive
                    archive._extract(z, "library.db", folder / name)
                    check = sqlite3.connect(folder / name)
                    try:  # it is a database, and it holds a library
                        check.execute("SELECT count(*) FROM stories").fetchone()
                    finally:
                        check.close()
                    archive._pictures(self.conn, z)  # named by their bytes: adding is harmless
            except (zipfile.BadZipFile, sqlite3.DatabaseError) as e:
                (folder / name).unlink(missing_ok=True)
                raise archive.BadArchive(f"what came down is not a library ({e}).") from None
            except archive.BadArchive:
                (folder / name).unlink(missing_ok=True)
                raise
        backups.request_restore(self.db_path, name)
        self._in_step_with(revision)
        return {"restart": True, "revision": revision}
