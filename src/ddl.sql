-- ===== base =====
CREATE SCHEMA IF NOT EXISTS ext;
CREATE EXTENSION IF NOT EXISTS citext     WITH SCHEMA ext;
CREATE EXTENSION IF NOT EXISTS pgcrypto   WITH SCHEMA ext;

CREATE SCHEMA IF NOT EXISTS app;

DO $do$
BEGIN
  BEGIN
    CREATE TYPE app.domain_state AS ENUM ('active','ddos','downtime');
  EXCEPTION WHEN duplicate_object THEN NULL;
  END;
END
$do$ LANGUAGE plpgsql;

-- ===== users =====
CREATE TABLE IF NOT EXISTS app.app_user (
  id             BIGSERIAL PRIMARY KEY,
  login          ext.citext NOT NULL UNIQUE,
  password_hash  TEXT       NOT NULL,
  is_admin       BOOLEAN    NOT NULL DEFAULT FALSE,
  created_at     TIMESTAMP  NOT NULL DEFAULT now()
);

-- ===== tracked domains =====
CREATE TABLE IF NOT EXISTS app.tracked_domain (
  id               BIGSERIAL PRIMARY KEY,
  user_id          BIGINT NOT NULL REFERENCES app.app_user(id) ON DELETE CASCADE,
  domain           TEXT   NOT NULL,
  submitted_at     TIMESTAMP NOT NULL DEFAULT now(),
  current_state    app.domain_state NOT NULL DEFAULT 'active',
  state_changed_at TIMESTAMP NOT NULL DEFAULT now(),
  CONSTRAINT uq_user_domain UNIQUE (user_id, domain),
  CONSTRAINT chk_domain_format CHECK (domain ~ '^[A-Za-z0-9-]+(\.[A-Za-z0-9-]+)+$')
);
CREATE INDEX IF NOT EXISTS idx_tracked_domain_domain ON app.tracked_domain (lower(domain));
CREATE INDEX IF NOT EXISTS idx_tracked_domain_state  ON app.tracked_domain (current_state);

-- ===== журнал смен статусов =====
CREATE TABLE IF NOT EXISTS app.domain_state_log (
  id          BIGSERIAL PRIMARY KEY,
  domain_id   BIGINT NOT NULL REFERENCES app.tracked_domain(id) ON DELETE CASCADE,
  event_ts    TIMESTAMP NOT NULL,
  prev_state  app.domain_state,
  new_state   app.domain_state NOT NULL,
  details     JSONB
);
CREATE INDEX IF NOT EXISTS idx_domain_state_log_d_ts ON app.domain_state_log(domain_id, event_ts);
CREATE INDEX IF NOT EXISTS idx_domain_state_log_new  ON app.domain_state_log(new_state);

-- ===== метрики =====
CREATE TABLE IF NOT EXISTS app.metric_sample (
  id             BIGSERIAL PRIMARY KEY,
  domain_id      BIGINT NOT NULL REFERENCES app.tracked_domain(id) ON DELETE CASCADE,
  ts             TIMESTAMP NOT NULL,
  packets_per_s  INTEGER NOT NULL CHECK (packets_per_s >= 0),
  uniq_ips       INTEGER NOT NULL CHECK (uniq_ips >= 0),
  bytes_per_s    BIGINT  NOT NULL CHECK (bytes_per_s >= 0),
  ok             BOOLEAN NOT NULL,
  source         TEXT NOT NULL,
  src_ips        INET[] NOT NULL DEFAULT '{}',
  extra          JSONB
);
CREATE INDEX IF NOT EXISTS idx_metric_sample_d_ts ON app.metric_sample(domain_id, ts);

-- ===== функция смены статуса =====
CREATE OR REPLACE FUNCTION app.fn_set_domain_state(
  p_domain_id BIGINT,
  p_new_state app.domain_state,
  p_ts        TIMESTAMP DEFAULT now(),
  p_details   JSONB       DEFAULT NULL
) RETURNS VOID
LANGUAGE plpgsql
AS $do$
DECLARE
  v_prev app.domain_state;
BEGIN
  SELECT current_state INTO v_prev
  FROM app.tracked_domain
  WHERE id = p_domain_id
  FOR UPDATE;

  IF v_prev IS DISTINCT FROM p_new_state THEN
    INSERT INTO app.domain_state_log(domain_id, event_ts, prev_state, new_state, details)
    VALUES (p_domain_id, p_ts, v_prev, p_new_state, p_details);

    UPDATE app.tracked_domain
    SET current_state = p_new_state,
        state_changed_at = p_ts
    WHERE id = p_domain_id;
  END IF;
END;
$do$;

-- ===== представления =====
DROP VIEW IF EXISTS app.v_domain_current_state;

CREATE VIEW app.v_domain_current_state AS
SELECT
  d.id                                AS domain_id,
  d.user_id,
  d.domain,
  d.current_state                     AS state,
  date_trunc('second', d.state_changed_at) AS started_at,
  date_trunc('second', d.submitted_at)     AS tracking_started
FROM app.tracked_domain d;

CREATE OR REPLACE VIEW app.v_ddos_events_last_hour AS
SELECT d.domain, l.event_ts
FROM app.domain_state_log l
JOIN app.tracked_domain d ON d.id = l.domain_id
WHERE l.new_state = 'ddos'
  AND l.event_ts >= (now() - interval '1 hour');
