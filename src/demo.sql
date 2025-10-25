-- ===========================================
-- DEMO DATA for app schema
-- безопасно перезапускается (idempotent-ish)
-- ===========================================
SET search_path = app, public, ext;

-- --- страховка: базовые объекты должны существовать (как в вашем ddl.sql) ---
DO $$
BEGIN
  BEGIN
    CREATE TYPE app.domain_state AS ENUM ('active','ddos','downtime');
  EXCEPTION WHEN duplicate_object THEN NULL;
  END;
END$$;

-- --- защищаем колонку is_admin (если включили защитный триггер из ddl.sql) ---
CREATE TABLE IF NOT EXISTS app.protected_column(
  schema_name  text NOT NULL,
  table_name   text NOT NULL,
  column_name  text NOT NULL,
  reason       text NOT NULL,
  PRIMARY KEY (schema_name, table_name, column_name)
);

INSERT INTO app.protected_column(schema_name, table_name, column_name, reason)
VALUES ('app','app_user','is_admin','Используется в register_user() / authenticate().')
ON CONFLICT (schema_name, table_name, column_name) DO UPDATE
SET reason = EXCLUDED.reason;

-- ===========================================
-- USERS
-- поля подобраны под типичную схему: id PK, login/email, passhash, is_admin, created_at
-- если у вас другая колонка для логина (например, email), просто подправьте INSERT-ы ниже
-- ===========================================

-- очистим демо-пользователей по логинам, чтобы не плодить дубликаты
DELETE FROM app.app_user WHERE login IN ('admin','alice','bob');

-- если у вас используется pgcrypto, сохраним дамми-хеш; иначе можно хранить как текст
-- (при необходимости замените на register_user('login','pass',is_admin=>true/false))
INSERT INTO app.app_user (login, password_hash, is_admin, created_at)
VALUES
  ('admin', crypt('admin123', gen_salt('bf')), TRUE,  now()),
  ('alice', crypt('alice123', gen_salt('bf')), FALSE, now()),
  ('bob',   crypt('bob123',   gen_salt('bf')), FALSE, now());

-- выберем id созданных юзеров
WITH u AS (
  SELECT login, id FROM app.app_user WHERE login IN ('admin','alice','bob')
)
SELECT * FROM u;  -- просто чтобы было что увидеть при выполнении в psql/IDE

-- ===========================================
-- TRACKED DOMAINS
-- структура из вашего ddl: (id PK), user_id FK -> app_user(id),
-- domain text UNIQUE per user, current_state app.domain_state, timestamps
-- ===========================================

-- подчистим только наши демо-домены (по доменным именам)
DELETE FROM app.tracked_domain
WHERE domain IN (
  'example.com','status.example.com','shop.example.com',
  'aliceblog.org','images.aliceblog.org',
  'bob-service.net','api.bob-service.net'
);

-- вставим выборку доменов: у каждого пользователя по 2–3 домена с разными статусами
INSERT INTO app.tracked_domain (user_id, domain, current_state, submitted_at, state_changed_at)
SELECT u.id, d.domain, d.state, d.submitted_at, d.state_changed_at
FROM app.app_user u
JOIN (
  VALUES
    -- alice
    ('alice', 'aliceblog.org',        'active'::app.domain_state,  now() - interval '20 days', now() - interval '5 days'),
    ('alice', 'images.aliceblog.org', 'active'::app.domain_state,    now() - interval '2 days',  now() - interval '45 minutes'),

    -- bob
    ('bob',   'bob-service.net',      'active'::app.domain_state,  now() - interval '14 days', now() - interval '1 day'),
    ('bob',   'api.bob-service.net',  'active'::app.domain_state,    now() - interval '1 day',   now() - interval '10 minutes')
) AS d(login, domain, state, submitted_at, state_changed_at)
  ON TRUE
WHERE u.login = d.login;

-- ===========================================
-- DOMAIN STATE LOG
-- допустим структура: (id PK), domain_id FK -> tracked_domain(id),
-- event_ts timestamp, new_state app.domain_state
-- если у вас другие имена/поля — поменяйте SELECT-часть ниже
-- ===========================================

-- очищаем только свежие наши события (по доменам из демо)
DELETE FROM app.domain_state_log l
USING app.tracked_domain td
WHERE l.domain_id = td.id
  AND td.domain IN (
    'example.com','status.example.com','shop.example.com',
    'aliceblog.org','images.aliceblog.org',
    'bob-service.net','api.bob-service.net'
  )
  AND l.event_ts > now() - interval '30 days';

-- нагенерим историю изменений последних дней/часов
WITH td AS (
  SELECT id, domain, current_state, state_changed_at
  FROM app.tracked_domain
  WHERE domain IN (
    'example.com','status.example.com','shop.example.com',
    'aliceblog.org','images.aliceblog.org',
    'bob-service.net','api.bob-service.net'
  )
),
ins AS (
  -- пример: каждая запись получает 2–3 события перед текущим состоянием
  SELECT
    id AS domain_id,
    domain,
    (state_changed_at - interval '3 days') AS event1_ts,
    CASE current_state
      WHEN 'active'   THEN 'ddos'::app.domain_state
      WHEN 'ddos'     THEN 'active'::app.domain_state
      WHEN 'downtime' THEN 'active'::app.domain_state
    END AS event1_state,
    (state_changed_at - interval '1 day') AS event2_ts,
    CASE current_state
      WHEN 'active'   THEN 'downtime'::app.domain_state
      WHEN 'ddos'     THEN 'downtime'::app.domain_state
      WHEN 'downtime' THEN 'ddos'::app.domain_state
    END AS event2_state
  FROM td
)
INSERT INTO app.domain_state_log (domain_id, event_ts, new_state)
SELECT domain_id, event1_ts, event1_state FROM ins
UNION ALL
SELECT domain_id, event2_ts, event2_state FROM ins
UNION ALL
-- добавим финальное событие на текущее состояние (чтобы лог соответствовал колонке current_state)
SELECT td.id, td.state_changed_at, td.current_state
FROM td;

-- ===========================================
-- QUICK CHECKS
-- ===========================================
-- 1) Текущие домены с состояниями
SELECT domain, current_state, state_changed_at
FROM app.tracked_domain
ORDER BY lower(domain);

-- 2) DDOS-события за последний час (для вашей v_ddos_events_last_hour)
SELECT d.domain, l.event_ts
FROM app.domain_state_log l
JOIN app.tracked_domain d ON d.id = l.domain_id
WHERE l.new_state = 'ddos'
  AND l.event_ts >= (now() - interval '1 hour')
ORDER BY l.event_ts DESC;

-- 3) Убедимся, что is_admin защищён (если подключён event trigger)
-- попытка удалить должна падать:
-- ALTER TABLE app.app_user DROP COLUMN is_admin;
