-- Cloud save for the desktop (docs/specs/2026-10-02-kataki-online.md §8): a computer linked to
-- an account, and the snapshots of its library that account keeps.

-- a link being made: the desktop holds `secret`, the person types or opens `code` while signed in
CREATE TABLE device_link(
  code text PRIMARY KEY,
  secret_hash text NOT NULL UNIQUE,
  name text NOT NULL,
  user_id text,                             -- set when the signed-in person approves it
  expires_at timestamptz NOT NULL
);

-- a linked computer: its token opens the cloud routes and nothing else
CREATE TABLE device(
  id text PRIMARY KEY,
  user_id text NOT NULL,
  token_hash text NOT NULL UNIQUE,
  name text NOT NULL,
  created_at timestamptz NOT NULL DEFAULT now(),
  last_used_at timestamptz
);
CREATE INDEX ix_device_user ON device(user_id);

-- one row per kept snapshot; the file is <cloud dir>/<user_id>/<revision>.kataki
CREATE TABLE snapshot(
  user_id text NOT NULL,
  revision integer NOT NULL,
  bytes bigint NOT NULL,
  holds jsonb NOT NULL,                     -- what the desktop said is in it: stories, characters, …
  device text NOT NULL,                     -- the name of the computer that sent it
  at timestamptz NOT NULL DEFAULT now(),
  PRIMARY KEY (user_id, revision)
);
