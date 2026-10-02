-- The ledger (docs/specs/2026-10-02-kataki-online.md §3): append-only, integer micro-dollars.
-- Balance = sum(credit.micros) - sum(usage.micros).
CREATE TABLE credit(
  id bigserial PRIMARY KEY,
  user_id text NOT NULL,
  micros bigint NOT NULL,
  reason text NOT NULL CHECK (reason IN ('starter', 'topup', 'refund', 'adjust')),
  ref text UNIQUE,                          -- what makes a grant happen once (starter:<user>, a payment id)
  at timestamptz NOT NULL DEFAULT now()
);
CREATE INDEX ix_credit_user ON credit(user_id);

CREATE TABLE usage(
  usage_id text PRIMARY KEY,                -- the engine's usage_log.usage_id: billed once
  user_id text NOT NULL,
  micros bigint NOT NULL CHECK (micros >= 0),
  role text NOT NULL,
  model text NOT NULL,
  prompt_tokens integer NOT NULL,
  cached_tokens integer NOT NULL,
  completion_tokens integer NOT NULL,
  estimated boolean NOT NULL,
  used_at timestamptz NOT NULL,             -- when the call was made (the engine's clock, UTC)
  at timestamptz NOT NULL DEFAULT now()
);
CREATE INDEX ix_usage_user ON usage(user_id);
