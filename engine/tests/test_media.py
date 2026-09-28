"""Images in the library: stored by their content beside the library, served with the token."""

import re

import pytest
from fastapi.testclient import TestClient

from kataki.server import create_app

PNG = b"\x89PNG\r\n\x1a\n" + b"\x00" * 64
NO_AUTH = {"Authorization": ""}  # what an <img src> sends: no header, only the query token


@pytest.fixture
def api(conn, backend):
    client = TestClient(create_app(conn, "t", llm=backend.llm, worker_delay=60))
    client.headers["Authorization"] = "Bearer t"
    with client:
        yield client


def test_an_image_round_trips_and_the_same_bytes_get_the_same_name(api, tmp_path):
    first = api.post("/media", content=PNG)
    assert first.status_code == 201
    name = first.json()["name"]
    assert re.fullmatch(r"[0-9a-f]{64}\.png", name) and first.json()["bytes"] == len(PNG)
    assert api.post("/media", content=PNG).json()["name"] == name
    assert (tmp_path / "blobs" / name).read_bytes() == PNG  # beside the library db

    got = api.get(f"/media/{name}?token=t", headers=NO_AUTH)
    assert got.status_code == 200 and got.content == PNG
    assert got.headers["content-type"] == "image/png"
    assert got.headers["x-content-type-options"] == "nosniff"
    assert got.headers["cache-control"] == "private, max-age=31536000, immutable"


def test_jpeg_gif_and_webp_are_recognised_by_their_bytes(api):
    for body, ext in [
        (b"\xff\xd8\xff\xe0" + b"\x00" * 16, "jpg"),
        (b"GIF87a" + b"\x00" * 16, "gif"),
        (b"GIF89a" + b"\x00" * 16, "gif"),
        (b"RIFF\x10\x00\x00\x00WEBPVP8 " + b"\x00" * 16, "webp"),
    ]:
        assert api.post("/media", content=body).json()["name"].endswith("." + ext)


@pytest.mark.parametrize(
    "body",
    [
        b'<svg xmlns="http://www.w3.org/2000/svg"><script>alert(1)</script></svg>',
        b"<html><body>hi</body></html>",
        b"just some text",
        b"RIFF\x10\x00\x00\x00WAVEfmt ",  # RIFF, but not WebP
    ],
)
def test_anything_else_is_refused(api, body):
    refused = api.post("/media", content=body)
    assert refused.status_code == 415
    assert refused.json()["detail"] == "Only PNG, JPEG, GIF or WebP images."


def test_an_image_over_20_mib_is_refused(api, tmp_path):
    assert api.post("/media", content=PNG + b"\x00" * (20 * 1024 * 1024)).status_code == 413
    assert not (tmp_path / "blobs").exists() or not any((tmp_path / "blobs").iterdir())


@pytest.mark.parametrize(
    "name", ["..%2Flibrary.db", "library.db", "abc.png", "0" * 64 + ".svg", "0" * 64 + ".png"]
)
def test_only_stored_images_are_served_and_only_by_their_exact_names(api, name):
    assert api.get(f"/media/{name}").status_code == 404


def test_the_query_token_opens_media_and_nothing_else(api):
    name = api.post("/media", content=PNG).json()["name"]
    assert api.get(f"/media/{name}", headers=NO_AUTH).status_code == 401
    assert api.get(f"/media/{name}?token=wrong", headers=NO_AUTH).status_code == 401
    assert api.get("/stories?token=t", headers=NO_AUTH).status_code == 401
    assert api.post("/media?token=t", content=PNG, headers=NO_AUTH).status_code == 401
