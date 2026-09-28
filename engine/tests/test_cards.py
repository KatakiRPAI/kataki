"""Character cards coming in: a PNG, a JSON file or a CHARX zip becomes a friend.

The fixtures are built here rather than checked in, so the file format is written down in one
place and the repository keeps no binaries.
"""

import base64
import io
import json
import struct
import zipfile
import zlib

import pytest
from fastapi.testclient import TestClient

from kataki import cards, library, media
from kataki.server import create_app

V3 = {
    "name": "Mira Vale",
    "nickname": "Mira",
    "description": "{{char}} keeps the ledger at the Gull and misses nothing.",
    "personality": "Watchful. Dry. Slow to trust, and then entirely.",
    "scenario": "Low tide at the docks; {{user}} has come asking after a name.",
    "first_mes": "*{{char}} sets down the glass she was drying* You're late.",
    "mes_example": "<START>\n{{user}}: Who was he?\n{{char}}: Nobody worth the ink.",
    "tags": ["noir", "harbour"],
    "creator": "someone",
    "character_version": "1.2",
    "creator_notes": "She lies about the ledger exactly once.",
    "system_prompt": "",
    "post_history_instructions": "",
    "alternate_greetings": ["*she doesn't look up* We're closed.", "You again."],
    "group_only_greetings": [],
    "extensions": {"depth_prompt": {"depth": 4}},
    "character_book": {"name": "The Gull", "entries": [{"keys": ["ledger"], "content": "green"}]},
}


def chunk(kind: bytes, body: bytes) -> bytes:
    return struct.pack(">I", len(body)) + kind + body + struct.pack(">I", zlib.crc32(kind + body))


def png(**text: bytes) -> bytes:
    """A real 1x1 PNG carrying tEXt chunks, which is how a card travels."""
    parts = [b"\x89PNG\r\n\x1a\n", chunk(b"IHDR", struct.pack(">IIBBBBB", 1, 1, 8, 2, 0, 0, 0))]
    parts += [chunk(b"tEXt", k.encode() + b"\x00" + v) for k, v in text.items()]
    parts += [chunk(b"IDAT", zlib.compress(b"\x00\xff\xff\xff")), chunk(b"IEND", b"")]
    return b"".join(parts)


def carded(spec: str, version: str, data: dict) -> bytes:
    """The base64 of a card's JSON, which is what a tEXt chunk holds."""
    card = {"spec": spec, "spec_version": version, "data": data}
    return base64.b64encode(json.dumps(card).encode())


def charx(data: dict, files: dict[str, bytes]) -> bytes:
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w") as z:
        z.writestr("card.json", json.dumps({"spec": "chara_card_v3", "data": data}))
        for path, body in files.items():
            z.writestr(path, body)
    return buf.getvalue()


@pytest.fixture
def api(conn, backend):
    client = TestClient(create_app(conn, "t", llm=backend.llm, worker_delay=60))
    client.headers["Authorization"] = "Bearer t"
    with client:
        yield client


def test_a_v3_png_becomes_a_friend_with_everything_the_card_said(conn):
    blob = png(ccv3=carded("chara_card_v3", "3.0", V3))
    made = cards.add(conn, blob)
    item = made["item"]

    assert made["spec"] == "chara_card_v3"
    assert item["kind"] == "character" and item["name"] == "Mira Vale"
    # description, personality and scenario are one card, in the engine's own bracket voice,
    # and `{{char}}` is her nickname where a card gives one, which is what V3 asks for
    assert item["description"] == (
        "Mira keeps the ledger at the Gull and misses nothing.\n\n"
        "[Personality]\nWatchful. Dry. Slow to trust, and then entirely.\n\n"
        "[Scenario]\nLow tide at the docks; {{user}} has come asking after a name."
    )
    assert item["data"]["first_message"] == "*Mira sets down the glass she was drying* You're late."
    assert "{{char}}" not in item["data"]["example_dialogue"]
    assert item["data"]["aliases"] == ["Mira"]  # the nickname is a name she answers to
    assert item["tags"] == ["harbour", "noir"]

    kept = item["data"]["card"]
    assert kept["creator"] == "someone" and kept["character_version"] == "1.2"
    assert kept["creator_notes"].startswith("She lies")
    assert len(kept["alternate_greetings"]) == 2
    assert kept["character_book"]["entries"][0]["keys"] == ["ledger"]
    assert kept["extensions"] == {"depth_prompt": {"depth": 4}}
    assert kept["spec"] == "chara_card_v3" and kept["spec_version"] == "3.0"

    portrait = item["data"]["portrait"]
    assert media.find(conn, portrait).read_bytes() == blob  # the card's own picture


def test_the_notes_say_what_was_kept_but_not_used(conn):
    made = cards.add(conn, png(ccv3=carded("chara_card_v3", "3.0", V3)))
    notes = " ".join(made["notes"])
    assert "2 other greetings" in notes
    assert "lorebook" in notes and "1" in notes


def test_ccv3_wins_over_chara_when_a_png_carries_both(conn):
    old = dict(V3, name="Mira (old)", description="the V2 copy")
    blob = png(chara=carded("chara_card_v2", "2.0", old), ccv3=carded("chara_card_v3", "3.0", V3))
    assert cards.add(conn, blob)["item"]["name"] == "Mira Vale"


def test_a_v2_png_a_v1_json_and_a_bare_v3_json_all_come_in(conn):
    two = cards.add(conn, png(chara=carded("chara_card_v2", "2.0", V3)))
    assert two["spec"] == "chara_card_v2" and two["item"]["name"] == "Mira Vale"

    one = {"name": "Tobin", "description": "A fence with a bad cough.", "first_mes": "Mm."}
    flat = cards.add(conn, json.dumps(one).encode())
    assert flat["spec"] == "chara_card_v1"
    assert flat["item"]["description"] == "A fence with a bad cough."
    assert flat["item"]["data"]["first_message"] == "Mm."
    assert flat["item"]["data"].get("portrait") is None  # a JSON card carries no picture

    bare = cards.add(conn, json.dumps({"spec": "chara_card_v3", "data": V3}).encode())
    assert bare["item"]["name"] == "Mira Vale"


def test_a_charx_takes_its_portrait_from_the_asset_the_card_points_at(conn):
    icon, other = png(), png(note=b"x")
    data = dict(
        V3,
        assets=[
            {"type": "background", "uri": "embeded://assets/background/images/bg.png",
             "name": "main", "ext": "png"},
            {"type": "icon", "uri": "embeded://assets/icon/images/face.png",
             "name": "main", "ext": "png"},
        ],
    )  # fmt: skip
    blob = charx(
        data, {"assets/icon/images/face.png": icon, "assets/background/images/bg.png": other}
    )
    item = cards.add(conn, blob)["item"]
    assert (
        media.find(conn, item["data"]["portrait"]).read_bytes() == icon
    )  # not the zip, not the bg


def test_a_card_can_say_its_picture_in_the_uri_itself(conn):
    face = png()
    uri = "data:image/png;base64," + base64.b64encode(face).decode()
    data = dict(V3, assets=[{"type": "icon", "uri": uri, "name": "main", "ext": "png"}])
    item = cards.add(conn, json.dumps({"spec": "chara_card_v3", "data": data}).encode())["item"]
    assert media.find(conn, item["data"]["portrait"]).read_bytes() == face


def test_a_picture_on_the_web_is_not_fetched(conn):
    data = dict(V3, assets=[{"type": "icon", "uri": "https://example.com/f.png",
                             "name": "main", "ext": "png"}])  # fmt: skip
    made = cards.add(conn, json.dumps({"spec": "chara_card_v3", "data": data}).encode())
    assert made["item"]["data"].get("portrait") is None
    assert any("example.com" in n for n in made["notes"])


def test_importing_the_same_card_twice_makes_two_friends(conn):
    blob = png(ccv3=carded("chara_card_v3", "3.0", V3))
    first, second = cards.add(conn, blob)["item"], cards.add(conn, blob)["item"]
    assert first["id"] != second["id"] and first["name"] == second["name"]
    assert len(library.list_items(conn, "character")) == 2
    assert first["data"]["portrait"] == second["data"]["portrait"]  # one file, by its bytes


def test_what_is_not_a_card_says_so_plainly(conn):
    for blob, says in [
        (b"not a card at all", "PNG, a JSON card or a CHARX"),
        (png(), "no character card"),
        (png(ccv3=b"!!!not base64!!!"), "could not be read"),
        (png(ccv3=base64.b64encode(b"{not json")), "could not be read"),
        (
            json.dumps({"spec": "chara_card_v3", "data": {"description": "no name"}}).encode(),
            "name",
        ),
        (charx({"name": "x"}, {})[:40], "could not be read"),
    ]:
        with pytest.raises(cards.BadCard, match=says):
            cards.add(conn, blob)

    empty = io.BytesIO()
    with zipfile.ZipFile(empty, "w") as z:
        z.writestr("readme.txt", "nothing here")
    with pytest.raises(cards.BadCard, match="card.json"):
        cards.add(conn, empty.getvalue())


def test_a_card_that_is_too_big_is_refused(conn):
    with pytest.raises(cards.BadCard, match="too big"):
        cards.add(conn, b"\x89PNG\r\n\x1a\n" + b"\x00" * cards.MAX_BYTES)


def test_the_route_brings_a_card_in_and_the_library_shows_it(api, conn):
    blob = png(ccv3=carded("chara_card_v3", "3.0", V3))
    made = api.post("/import/card", content=blob)
    assert made.status_code == 201
    item = made.json()["item"]
    assert item["name"] == "Mira Vale" and made.json()["notes"]

    assert [i["name"] for i in api.get("/library").json()] == ["Mira Vale"]
    got = api.get(f"/media/{item['data']['portrait']}")
    assert got.status_code == 200 and got.content == blob

    assert api.post("/import/card", content=b"nonsense").status_code == 422


def test_a_story_started_from_an_imported_card_reads_as_itself(api, backend):
    """The end of it: her greeting says her name, and the prompt says who the player is —
    no card macro survives into anything the model or the reader sees."""
    provider = api.post("/providers", json={"name": "local", "base_url": "http://fake/v1/"}).json()
    api.put("/roles/rp", json={"provider_id": provider["id"], "model": "rp-model"})
    item = api.post("/import/card", content=png(ccv3=carded("chara_card_v3", "3.0", V3))).json()
    me = api.post("/library", json={"kind": "character", "name": "Aren", "data": {"persona": True}})
    story = api.post(
        "/stories",
        json={"title": "Low Tide", "character_ids": [item["item"]["id"]],
              "persona_id": me.json()["id"]},
    ).json()  # fmt: skip
    [opening] = api.get(f"/stories/{story['id']}/messages").json()
    assert opening["text"] == "*Mira sets down the glass she was drying* You're late."

    backend.say("*she turns the page* Ask, then.")
    api.post(f"/stories/{story['id']}/turn", json={"text": "Who was he?"})
    sent = json.dumps(backend.requests[-1]["messages"])
    assert "{{" not in sent and "<char>" not in sent
    assert "Aren has come asking after a name" in sent  # the player, by the name she knows


# --- what the review found: a hostile or merely messy card ---------------------------------


def test_the_short_name_is_the_one_she_is_called_by(conn):
    """V3: `{{char}}` is the nickname when a card gives one, and the full name when it does not.
    The library keeps the full name either way."""
    named = dict(V3, name="Hatsune Miku (Vocaloid)", nickname="Miku",
                 first_mes="*{{char}} waves* Hi, {{user}}!")  # fmt: skip
    item = cards.add(conn, json.dumps({"spec": "chara_card_v3", "data": named}).encode())["item"]
    assert item["name"] == "Hatsune Miku (Vocaloid)"
    assert item["data"]["first_message"] == "*Miku waves* Hi, {{user}}!"

    plain = dict(V3, name="Tobin", first_mes="*{{char}} coughs*")
    plain.pop("nickname")
    alone = cards.add(conn, json.dumps({"spec": "chara_card_v3", "data": plain}).encode())["item"]
    assert alone["data"]["first_message"] == "*Tobin coughs*"
    assert alone["data"]["aliases"] == []


def test_a_nickname_that_is_the_name_in_other_letters_is_not_a_second_name(conn):
    """Aliases are case-blind in the schema, so MIRA/Mira must not be two rows — the story
    that started from her is what used to break."""
    card = {"name": "MIRA", "nickname": "Mira", "first_mes": "hm."}
    item = cards.add(conn, json.dumps({"spec": "chara_card_v3", "data": card}).encode())["item"]
    assert item["data"]["aliases"] == []
    story = library.create_story(conn, "Low Tide", character_ids=[item["id"]])
    assert conn.execute("SELECT count(*) FROM messages WHERE story_id=?", (story,)).fetchone()[0]


def test_tags_that_are_not_a_list_are_not_tags(conn):
    """A string is iterable; its letters are not an index of the library."""
    item = cards.add(conn, json.dumps({"name": "Tobin", "tags": "noir,harbour"}).encode())["item"]
    assert item["tags"] == []
    assert library.all_tags(conn) == []


def test_a_charx_that_promises_to_become_enormous_is_refused(conn):
    """A small archive that unpacks to gigabytes is the oldest trick there is."""
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as z:
        z.writestr("card.json", json.dumps({"data": dict(V3, description="A" * 64_000_000)}))
    bomb = buf.getvalue()
    assert len(bomb) < 100_000  # tiny on the way in
    with pytest.raises(cards.BadCard, match="card.json"):
        cards.add(conn, bomb)


def test_only_the_pictures_a_card_points_at_are_unpacked(conn):
    """Sixty large members in one archive, one of them named: the other fifty-nine are never
    read, so the memory an import can cost is what the card actually uses."""
    face = png()
    data = dict(V3, assets=[{"type": "icon", "uri": "embeded://assets/icon/face.png",
                             "name": "main", "ext": "png"}])  # fmt: skip
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as z:
        z.writestr("card.json", json.dumps({"spec": "chara_card_v3", "data": data}))
        z.writestr("assets/icon/face.png", face)
        for i in range(60):
            z.writestr(f"assets/other/{i}.bin", b"\0" * 9_000_000)  # 540 MB, were we to read it
    blob = buf.getvalue()
    assert len(blob) < 1_000_000  # small on the way in, as these always are

    item = cards.add(conn, blob)["item"]
    assert media.find(conn, item["data"]["portrait"]).read_bytes() == face


def tampered(blob: bytes, local_at: int, central_at: int, value: int) -> bytes:
    """A zip says the same thing twice, in the local header and in the directory at the end;
    change both, or the archive is merely inconsistent."""
    body = bytearray(blob)
    body[local_at : local_at + 2] = value.to_bytes(2, "little")
    where = body.find(b"PK\x01\x02")
    body[where + central_at : where + central_at + 2] = value.to_bytes(2, "little")
    return bytes(body)


def test_a_locked_or_broken_archive_is_a_bad_card_not_a_crash(conn):
    """Everything zipfile can throw arrives as the one error the route knows how to answer,
    not as a five hundred."""
    plain = charx(V3, {})
    locked = tampered(plain, 6, 8, 0x01)  # the general-purpose flag: this member is encrypted
    unreadable = tampered(plain, 8, 10, 99)  # a compression method nothing has a reader for
    broken = bytearray(plain)
    broken[40:46] = b"\x00" * 6  # the compressed bytes themselves, ruined

    for blob in (locked, unreadable, bytes(broken)):
        with pytest.raises(cards.BadCard, match="could not be read"):
            cards.add(conn, blob)


def test_a_picture_encoded_wrongly_costs_the_picture_and_nothing_else(conn):
    """One broken asset never fails an import: the friend still arrives, with a note."""
    made = cards.add(conn, png(**{"ccv3": carded("chara_card_v3", "3.0", V3),
                                  "chara-ext-asset_:a.png": b"QUJDR"}))  # fmt: skip
    assert made["item"]["name"] == "Mira Vale"

    data = dict(V3, assets=[{"type": "icon", "uri": "data:image/png;base64,QUJDR",
                             "name": "main", "ext": "png"}])  # fmt: skip
    broken = cards.add(conn, json.dumps({"spec": "chara_card_v3", "data": data}).encode())
    assert broken["item"]["data"].get("portrait") is None
    assert any("not an image" in n or "not in this file" in n for n in broken["notes"])


def test_a_picture_too_big_for_the_library_is_not_smuggled_in_as_a_card(conn):
    """`POST /media` refuses anything over media.MAX_BYTES; a card is not a way around that."""
    fat = png(**{"ccv3": carded("chara_card_v3", "3.0", V3), "bulk": b"\0" * (media.MAX_BYTES + 1)})
    made = cards.add(conn, fat)
    assert made["item"]["data"].get("portrait") is None
    assert any("larger than the library will hold" in n for n in made["notes"])


def test_the_player_is_the_player_even_when_their_character_is_out_of_the_room(api, backend):
    """`{{user}}` reads from the story, not from who happens to be standing here."""
    provider = api.post("/providers", json={"name": "local", "base_url": "http://fake/v1/"}).json()
    api.put("/roles/rp", json={"provider_id": provider["id"], "model": "rp-model"})
    her = dict(V3, description="{{char}} has known {{user}} since the war.")
    item = api.post("/import/card", content=png(ccv3=carded("chara_card_v3", "3.0", her))).json()
    me = api.post("/library", json={"kind": "character", "name": "Aren", "data": {"persona": True}})
    story = api.post(
        "/stories",
        json={"title": "Low Tide", "character_ids": [item["item"]["id"]],
              "persona_id": me.json()["id"]},
    ).json()["id"]  # fmt: skip
    cast = api.get(f"/stories/{story}/cast").json()["entities"]
    aren = next(e for e in cast if e["name"] == "Aren")
    api.post(f"/stories/{story}/presence", json={"entity_id": aren["id"], "present": False})

    backend.say("*she turns the page* Ask, then.")
    api.post(f"/stories/{story}/turn", json={"text": "Who was he?"})
    assert "Mira has known Aren since the war." in json.dumps(backend.requests[-1]["messages"])
