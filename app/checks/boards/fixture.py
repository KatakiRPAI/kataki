"""The boards' stories, for the side-by-side check: run on a library the app has already seeded
with the sample world (open /welcome/who once), so Home, Stories and the Scene have what the
boards show. Test data only; the shipped sample world has no stories.
    engine/.venv/Scripts/python.exe app/checks/boards/fixture.py <library.db>
"""

import sqlite3
import sys

from kataki import chat, library

conn = sqlite3.connect(sys.argv[1])
conn.row_factory = sqlite3.Row
conn.execute("PRAGMA foreign_keys=ON")
item = {r["name"]: r["id"] for r in conn.execute("SELECT id, name FROM lib_items")}
book = {r["title"]: r["id"] for r in conn.execute("SELECT id, title FROM books")}


def story(title, cast, persona, place, book_title, lines, ago, epoch=19 * 60):
    """`lines`: (speaker name, text, minutes skipped before it); the persona's lines are the user's."""
    sid = library.create_story(conn, title, [item[c] for c in cast], item[place], item[persona],
                               epoch_offset_min=epoch, opening=False)
    ent = {r["name"]: r["id"] for r in conn.execute("SELECT id, name FROM entities WHERE story_id=?", (sid,))}
    for who, text, skip in lines:
        role = "user" if who == persona else "assistant"
        chat.append_message(conn, sid, role, text, ent[who], skip_minutes=skip)
    with conn:
        conn.execute("UPDATE stories SET book_id=? WHERE id=?", (book.get(book_title), sid))
        conn.execute("UPDATE messages SET created_at=datetime('now', ?) WHERE story_id=?", (ago, sid))
    return sid


def memory(sid, knower, about, detail, belief=1.0, ago_min=0):
    """What `knower` holds about `about`, as the memory reader would have left it: `ago_min`
    story minutes old (older fades), `belief` under 0.7 reads as doubted."""
    ent = {r["name"]: r["id"] for r in conn.execute("SELECT id, name FROM entities WHERE story_id=?", (sid,))}
    mid = library.add_memory(conn, sid, detail, knower_ids=[ent[knower]], entity_ids=[ent[about]])
    with conn:
        conn.execute("UPDATE memories SET story_time=story_time-? WHERE id=?", (ago_min, mid))
        conn.execute("UPDATE knowledge SET belief=?, source='witnessed', learned_story_time=learned_story_time-? WHERE memory_id=?", (belief, ago_min, mid))


two = story("Two Sugars, No Title", ["Mike", "Theo"], "Liv", "Halcyon Coffee", "Close to the Crown", [
    ("Liv", "Still open? I’ll take anything hot, I don’t care what.", 0),
    ("Mike", "*flips the sign back around and goes for a cup* Ten minutes. Drink it fast or I’m putting you to work.", 0),
    ("Theo", "*drops his backpack on the counter* Did someone say free labour?", 0),
    ("Liv", "Theo, would you grab the milk from the back? All of it.", 0),
    ("Theo", "*picks up the crates, grinning* Anything for a paying customer.", 0),
    ("Liv", "Quickly, while he’s gone. My mother is the queen’s step-sister. I’m on the gala list and I don’t want to be. Tell no one.", 0),
    ("Mike", "*sets the cup down very carefully* Then stop saying it so loud. My mother cuts her hair.", 0),
    ("Mike", "You? *he looks at the jacket he borrowed, then at you* The list. You said you weren’t coming to this.", 21 * 1440 + 2),
    ("Liv", "I never said that. I said I didn’t want to be on it.", 0),
    ("Mike", "*frowns* …I could have sworn. Three weeks is a long time to hold one sentence.", 0),
], "-2 hours")
gala = story("The Gala List", ["Jae"], "Liv", "Corvel Palace", "Close to the Crown", [
    ("Liv", "Are you going?", 0),
    ("Jae", "Officially? No comment. Unofficially, be there by eight.", 0),
], "-7 days")
story("Three in the Morning", ["Nico"], "Liv", "The flat on Ardenne", "The Flat on Ardenne", [
    ("Liv", "You're still up.", 0),
    ("Nico", "You’re not going to like this painting.", 0),
], "-4 days")
story("The Long Way Home", ["Liv"], "Cas", "Halcyon Coffee", None, [
    ("Cas", "The engine's gone again.", 0),
    ("Liv", "Leave it. We’ll push.", 0),
], "-21 days")
memory(two, "Mike", "Liv", "Her mother is the queen’s step-sister.")
memory(two, "Mike", "Liv", "She did not want to be on the gala list.", ago_min=21 * 1440)
memory(two, "Mike", "Liv", "She says she never said it.", belief=0.5)
memory(two, "Theo", "Liv", "She sent him to the back for milk.")
memory(gala, "Jae", "Liv", "Her name is on the list.")
# P20 the first scene: Mike and his opening line only; P21 a story begun from a plot
first = library.create_story(conn, "Halcyon Coffee · Monday", [item["Mike"]], item["Halcyon Coffee"], item["Liv"], epoch_offset_min=19 * 60)
plot = library.create_story(conn, "The Invitation", [item["Mike"]], item["Halcyon Coffee"], item["Liv"], scenario_id=item["The Invitation"], epoch_offset_min=19 * 60 + 30)
with conn:  # a month old, so Home still leads with Two Sugars
    conn.execute("UPDATE messages SET created_at=datetime('now', '-30 days') WHERE story_id IN (?, ?)", (first, plot))
    conn.execute("UPDATE stories SET created_at=datetime('now', '-30 days') WHERE id IN (?, ?)", (first, plot))
print("ok")
