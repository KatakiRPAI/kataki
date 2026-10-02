-- What an account is charged for besides model calls (docs/specs/2026-10-02-kataki-online.md §8):
-- for now, cloud storage past the free limit, once a day. Append-only, integer micro-dollars.
-- Balance = sum(credit) - sum(usage) - sum(charge).
CREATE TABLE charge(
  id bigserial PRIMARY KEY,
  user_id text NOT NULL,
  micros bigint NOT NULL CHECK (micros >= 0),
  reason text NOT NULL CHECK (reason IN ('storage')),
  day date NOT NULL,                        -- the day it is for: charged once
  bytes bigint NOT NULL,                    -- what was kept that day
  at timestamptz NOT NULL DEFAULT now(),
  UNIQUE (user_id, reason, day)
);
CREATE INDEX ix_charge_user ON charge(user_id);
