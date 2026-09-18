-- Kataki RPAI library schema, version 1. Design: docs/specs/2026-09-18-m0-m1-design.md
--
-- run_id on a derived row points at the extraction run that produced it. NULL means
-- user/seed authored (always live). Deleting a run cascades to everything it derived,
-- which is how a retry stays idempotent. Derived rows are never updated in place:
-- truth is superseded, and flags/edges/knowledge/presence are append-only logs whose
-- current value is the latest live row at or before "now" in story time.

CREATE TABLE providers(
  id INTEGER PRIMARY KEY,
  name TEXT UNIQUE NOT NULL,
  base_url TEXT NOT NULL,
  extra TEXT NOT NULL DEFAULT '{}'
);

CREATE TABLE model_roles(
  role TEXT PRIMARY KEY CHECK(role IN('rp','narrator','utility','reasoning','embed','image','music')),
  provider_id INTEGER REFERENCES providers,
  model TEXT,                                   -- provider_id and model both NULL = inherit (chain lives in code)
  kind TEXT NOT NULL DEFAULT 'auto' CHECK(kind IN('auto','reasoning','standard')),  -- user override
  detected_kind TEXT CHECK(detected_kind IN('reasoning','standard')),               -- from the connection probe
  params TEXT NOT NULL DEFAULT '{}'             -- samplers, extra_body, id_slot, ctx_size, tok_ratio, thinking,
                                                -- reasoning_effort, think_budget_tokens, think_tags, show_thoughts
);

CREATE TABLE settings(key TEXT PRIMARY KEY, value TEXT NOT NULL);

CREATE TABLE lib_items(
  id INTEGER PRIMARY KEY,
  kind TEXT NOT NULL CHECK(kind IN('character','place','scenario')),
  name TEXT NOT NULL,
  description TEXT NOT NULL DEFAULT '',
  private TEXT NOT NULL DEFAULT '',
  data TEXT NOT NULL DEFAULT '{}',              -- first_message, example_dialogue, aliases[], card leftovers (M2)
  folder_id INTEGER,                            -- M2 seam
  media_id INTEGER,                             -- M3 seam
  created_at TEXT DEFAULT CURRENT_TIMESTAMP,
  updated_at TEXT
);

CREATE TABLE stories(
  id INTEGER PRIMARY KEY,
  title TEXT NOT NULL,
  scenario_id INTEGER REFERENCES lib_items,
  persona_entity_id INTEGER,
  active_leaf_id INTEGER,
  epoch_offset_min INTEGER NOT NULL DEFAULT 480,
  minutes_per_turn INTEGER NOT NULL DEFAULT 2,
  overrides TEXT NOT NULL DEFAULT '{}',         -- per-story settings, incl. overrides.roles
  book_id INTEGER,                              -- M2 seam
  created_at TEXT DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE messages(
  id INTEGER PRIMARY KEY,
  story_id INTEGER NOT NULL REFERENCES stories ON DELETE CASCADE,
  parent_id INTEGER REFERENCES messages ON DELETE CASCADE,
  role TEXT NOT NULL CHECK(role IN('user','assistant','system')),
  speaker_id INTEGER REFERENCES entities,
  text TEXT NOT NULL,
  story_time INTEGER NOT NULL,                  -- the clock AFTER this message, in story minutes
  skip_minutes INTEGER NOT NULL DEFAULT 0,
  scene_id INTEGER REFERENCES scenes,
  tokens INTEGER,
  hidden INTEGER NOT NULL DEFAULT 0,
  edited_at TEXT,
  gen TEXT,                                     -- generation metadata, incl. reasoning (never re-enters prompts)
  created_at TEXT DEFAULT CURRENT_TIMESTAMP
);
CREATE INDEX ix_msg_parent ON messages(parent_id);
CREATE INDEX ix_msg_story ON messages(story_id);

CREATE TABLE scenes(
  id INTEGER PRIMARY KEY,
  story_id INTEGER NOT NULL REFERENCES stories ON DELETE CASCADE,
  start_message_id INTEGER REFERENCES messages ON DELETE CASCADE,  -- NULL or on the active path = live
  place_id INTEGER REFERENCES entities,
  title TEXT,
  start_story_time INTEGER NOT NULL,
  mood TEXT,
  media  TEXT                                    -- M3/M4 seam
);

CREATE TABLE presence(                          -- append-only; current = last live row per entity
  id INTEGER PRIMARY KEY,
  scene_id INTEGER NOT NULL REFERENCES scenes ON DELETE CASCADE,
  entity_id INTEGER NOT NULL REFERENCES entities ON DELETE CASCADE,
  message_id INTEGER REFERENCES messages ON DELETE CASCADE,
  present INTEGER NOT NULL
);

CREATE TABLE entities(
  id INTEGER PRIMARY KEY,
  story_id INTEGER NOT NULL REFERENCES stories ON DELETE CASCADE,
  kind TEXT NOT NULL CHECK(kind IN('character','place','item','faction','other')),
  name TEXT NOT NULL,
  summary TEXT NOT NULL DEFAULT '',
  description TEXT,                             -- snapshot of the library template; the story may diverge
  private TEXT,
  lib_item_id INTEGER REFERENCES lib_items,
  is_ai INTEGER NOT NULL DEFAULT 0,
  origin_entity_id INTEGER,                     -- M2 cross-story link
  merge_candidate_id INTEGER REFERENCES entities,
  hidden INTEGER NOT NULL DEFAULT 0,
  run_id INTEGER REFERENCES extraction_runs(id) ON DELETE CASCADE
);
CREATE INDEX ix_ent_story ON entities(story_id, kind);

CREATE TABLE aliases(
  entity_id INTEGER NOT NULL REFERENCES entities ON DELETE CASCADE,
  alias TEXT NOT NULL COLLATE NOCASE,
  PRIMARY KEY(entity_id, alias)
) WITHOUT ROWID;

CREATE TABLE tags(id INTEGER PRIMARY KEY, name TEXT UNIQUE NOT NULL COLLATE NOCASE);

CREATE TABLE taggings(
  tag_id INTEGER NOT NULL REFERENCES tags ON DELETE CASCADE,
  obj TEXT NOT NULL CHECK(obj IN('lib_item','story','entity','memory')),
  obj_id INTEGER NOT NULL,
  PRIMARY KEY(tag_id, obj, obj_id)
) WITHOUT ROWID;
CREATE INDEX ix_taggings_obj ON taggings(obj, obj_id);

CREATE TABLE flags(                             -- typed state; validity = [story_time, next live row)
  id INTEGER PRIMARY KEY,
  entity_id INTEGER NOT NULL REFERENCES entities ON DELETE CASCADE,
  key TEXT NOT NULL COLLATE NOCASE,
  value TEXT,                                   -- NULL = cleared
  story_time INTEGER NOT NULL,
  private INTEGER NOT NULL DEFAULT 0,
  run_id INTEGER REFERENCES extraction_runs(id) ON DELETE CASCADE
);
CREATE INDEX ix_flags ON flags(entity_id, key, story_time);

CREATE TABLE edges(
  id INTEGER PRIMARY KEY,
  story_id INTEGER NOT NULL REFERENCES stories ON DELETE CASCADE,
  src_id INTEGER NOT NULL REFERENCES entities ON DELETE CASCADE,
  dst_id INTEGER NOT NULL REFERENCES entities ON DELETE CASCADE,
  rel TEXT NOT NULL,
  note TEXT,
  story_time INTEGER NOT NULL,
  ended INTEGER NOT NULL DEFAULT 0,
  run_id INTEGER REFERENCES extraction_runs(id) ON DELETE CASCADE
);
CREATE INDEX ix_edges_src ON edges(src_id);
CREATE INDEX ix_edges_dst ON edges(dst_id);

CREATE TABLE memories(                          -- world truth (event, fact) and what characters assert (claim)
  id INTEGER PRIMARY KEY,
  story_id INTEGER NOT NULL REFERENCES stories ON DELETE CASCADE,
  kind TEXT NOT NULL CHECK(kind IN('event','fact','claim')),
  story_time INTEGER NOT NULL,
  detail TEXT NOT NULL,                         -- rendered when the memory is SHARP
  gist TEXT NOT NULL,                           -- rendered when it is HAZY; both written once, at extraction
  importance INTEGER NOT NULL DEFAULT 5 CHECK(importance BETWEEN 1 AND 10),
  emotion TEXT,
  is_true INTEGER,                              -- NULL = unverified claim
  asserted_by INTEGER REFERENCES entities,      -- NULL = narration (truth, may supersede)
  supersedes_id INTEGER REFERENCES memories,
  covert INTEGER NOT NULL DEFAULT 0,            -- witnesses = participants only
  common INTEGER NOT NULL DEFAULT 0,            -- visible to everyone without a knowledge row
  pinned INTEGER NOT NULL DEFAULT 0,            -- lives in the stable primer block (lorebook seam)
  tags_text TEXT NOT NULL DEFAULT '',           -- mirror of taggings, for FTS recall
  from_message_id INTEGER,
  to_message_id INTEGER,
  hidden INTEGER NOT NULL DEFAULT 0,
  real_time TEXT DEFAULT CURRENT_TIMESTAMP,
  run_id INTEGER REFERENCES extraction_runs(id) ON DELETE CASCADE
);
CREATE INDEX ix_mem_story ON memories(story_id, story_time);
CREATE INDEX ix_mem_run ON memories(run_id);
CREATE INDEX ix_mem_sup ON memories(supersedes_id);

CREATE TABLE memory_entities(                   -- place and items are roles, so the req-2 clique exists by construction
  memory_id INTEGER NOT NULL REFERENCES memories ON DELETE CASCADE,
  entity_id INTEGER NOT NULL REFERENCES entities ON DELETE CASCADE,
  role TEXT NOT NULL CHECK(role IN('actor','target','witness','place','item','subject')),
  PRIMARY KEY(memory_id, entity_id, role)
) WITHOUT ROWID;
CREATE INDEX ix_me_entity ON memory_entities(entity_id);

CREATE VIRTUAL TABLE memories_fts USING fts5(
  detail, gist, tags_text,
  content='memories', content_rowid='id',
  tokenize='porter unicode61 remove_diacritics 2'
);
CREATE TRIGGER mem_ai AFTER INSERT ON memories BEGIN
  INSERT INTO memories_fts(rowid, detail, gist, tags_text) VALUES(new.id, new.detail, new.gist, new.tags_text);
END;
CREATE TRIGGER mem_ad AFTER DELETE ON memories BEGIN
  INSERT INTO memories_fts(memories_fts, rowid, detail, gist, tags_text)
    VALUES('delete', old.id, old.detail, old.gist, old.tags_text);
END;
CREATE TRIGGER mem_au AFTER UPDATE OF detail, gist, tags_text ON memories BEGIN
  INSERT INTO memories_fts(memories_fts, rowid, detail, gist, tags_text)
    VALUES('delete', old.id, old.detail, old.gist, old.tags_text);
  INSERT INTO memories_fts(rowid, detail, gist, tags_text) VALUES(new.id, new.detail, new.gist, new.tags_text);
END;

CREATE TABLE knowledge(                         -- who knows what, and how; current = MAX(id) among live rows
  id INTEGER PRIMARY KEY,
  knower_id INTEGER NOT NULL REFERENCES entities ON DELETE CASCADE,
  memory_id INTEGER NOT NULL REFERENCES memories ON DELETE CASCADE,
  source TEXT NOT NULL CHECK(source IN('witnessed','told','overheard','rumor','inferred','innate')),
  told_by_id INTEGER REFERENCES entities,
  learned_story_time INTEGER NOT NULL,
  fidelity REAL NOT NULL DEFAULT 0,             -- additive activation offset (0 witnessed … -1.5 rumor)
  belief REAL NOT NULL DEFAULT 1,               -- 0..1
  run_id INTEGER REFERENCES extraction_runs(id) ON DELETE CASCADE
);
CREATE INDEX ix_know ON knowledge(knower_id, memory_id);

CREATE TABLE accesses(                          -- the primary key IS the reinforcement cap: once per scene
  knower_id INTEGER NOT NULL,
  memory_id INTEGER NOT NULL REFERENCES memories ON DELETE CASCADE,
  scene_id INTEGER NOT NULL REFERENCES scenes ON DELETE CASCADE,
  kind TEXT NOT NULL CHECK(kind IN('recall','retold')),
  story_time INTEGER NOT NULL,
  sharp INTEGER NOT NULL,
  weight REAL NOT NULL,
  message_id INTEGER,
  PRIMARY KEY(knower_id, memory_id, scene_id, kind)
) WITHOUT ROWID;

CREATE TABLE embeddings(
  id INTEGER PRIMARY KEY,
  memory_id INTEGER REFERENCES memories ON DELETE CASCADE,
  entity_id INTEGER REFERENCES entities ON DELETE CASCADE,
  model TEXT NOT NULL,
  dim INTEGER NOT NULL,
  vec BLOB NOT NULL,                            -- float32 little-endian
  CHECK((memory_id IS NULL) <> (entity_id IS NULL))
);
CREATE UNIQUE INDEX ux_emb_m ON embeddings(memory_id, model) WHERE memory_id IS NOT NULL;
CREATE UNIQUE INDEX ux_emb_e ON embeddings(entity_id, model) WHERE entity_id IS NOT NULL;

CREATE TABLE summaries(
  id INTEGER PRIMARY KEY,
  story_id INTEGER NOT NULL REFERENCES stories ON DELETE CASCADE,
  scene_id INTEGER REFERENCES scenes ON DELETE CASCADE,
  to_message_id INTEGER,
  story_time INTEGER,
  text TEXT NOT NULL,
  tokens INTEGER,
  run_id INTEGER REFERENCES extraction_runs(id) ON DELETE CASCADE
);

CREATE TABLE extraction_runs(
  id INTEGER PRIMARY KEY,
  story_id INTEGER NOT NULL REFERENCES stories ON DELETE CASCADE,
  from_message_id INTEGER NOT NULL,
  to_message_id INTEGER NOT NULL,
  trigger TEXT NOT NULL,                        -- cadence | scene | skip | evict | manual
  status TEXT NOT NULL DEFAULT 'pending' CHECK(status IN('pending','running','ok','failed','cancelled')),
  stale INTEGER NOT NULL DEFAULT 0,
  attempts INTEGER NOT NULL DEFAULT 0,
  role TEXT,                                    -- which model role served the run
  model TEXT,
  raw TEXT,
  warnings TEXT,
  error TEXT,
  started_at TEXT,
  finished_at TEXT,
  UNIQUE(story_id, from_message_id, to_message_id)
);

CREATE TABLE context_log(
  id INTEGER PRIMARY KEY,
  story_id INTEGER NOT NULL REFERENCES stories ON DELETE CASCADE,
  message_id INTEGER REFERENCES messages ON DELETE CASCADE,
  speaker_id INTEGER,
  budget INTEGER,
  sections TEXT NOT NULL,                       -- [{name,tokens,cap,evicted}]
  memories TEXT NOT NULL,                       -- [{memory_id,tier,A,B,S,G,imp,F,noise,effortful,tokens}]
  prompt TEXT,                                  -- pruned to the last 20 per story
  est_tokens INTEGER,
  actual_tokens INTEGER,
  cached_tokens INTEGER,
  created_at TEXT DEFAULT CURRENT_TIMESTAMP
);
