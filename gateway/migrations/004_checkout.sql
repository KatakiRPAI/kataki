-- Top-ups (docs/specs/2026-10-02-kataki-online.md G7): a checkout opened for an amount, paid
-- (or not) at the payment processor; paying grants credit once (credit.ref = 'topup:<id>').
CREATE TABLE checkout(
  id text PRIMARY KEY,
  user_id text NOT NULL,
  micros bigint NOT NULL CHECK (micros > 0),
  processor text NOT NULL,                  -- 'test' until the owner's processor is wired in
  status text NOT NULL CHECK (status IN ('open', 'paid', 'cancelled')),
  ref text,                                 -- the processor's own id for the payment
  created_at timestamptz NOT NULL DEFAULT now(),
  settled_at timestamptz
);
CREATE INDEX ix_checkout_user ON checkout(user_id);
