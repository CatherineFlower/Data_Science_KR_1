import os
import re
import logging
from logging.handlers import RotatingFileHandler
from contextlib import contextmanager
from datetime import datetime, timezone
from pathlib import Path

import psycopg2
from psycopg2.extras import Json
from dotenv import load_dotenv

load_dotenv()

# -------------------- Логирование --------------------
logger = logging.getLogger("ddos_app.db")
logger.propagate = False
logger.setLevel(getattr(logging, os.getenv("LOG_LEVEL", "INFO").upper(), logging.INFO))

# === Настройка логирования ===
DB_LOG_CONN = os.getenv("DB_LOG_CONN", "0") == "1"          # 0 — не логировать коннекты; 1 — логировать (DEBUG)
DB_LOG_SQL_PREVIEW = os.getenv("DB_LOG_SQL_PREVIEW", "1") == "1"  # 1 — логировать превью DDL/DML на INFO

# только файл (без консоли)
LOG_FILE = os.getenv("LOG_FILE", "app.log")
LOG_MAX_BYTES = int(os.getenv("LOG_MAX_BYTES", "1048576"))
LOG_BACKUP_COUNT = int(os.getenv("LOG_BACKUP_COUNT", "3"))

if not any(isinstance(h, RotatingFileHandler) for h in logger.handlers):
    fh = RotatingFileHandler(LOG_FILE, maxBytes=LOG_MAX_BYTES, backupCount=LOG_BACKUP_COUNT, encoding="utf-8")
    fh.setLevel(logger.level)
    fh.setFormatter(logging.Formatter("%(asctime)s %(levelname)s %(name)s - %(message)s"))
    logger.addHandler(fh)

# -------------------- Конфигурация БД --------------------
PGHOST = os.getenv("PGHOST", "127.0.0.1")
PGPORT = int(os.getenv("PGPORT", "5432"))
PGDATABASE = os.getenv("PGDATABASE", "postgres")
PGUSER = os.getenv("PGUSER", "postgres")
PGPASSWORD = os.getenv("PGPASSWORD", "18")
DSN = f"host={PGHOST} port={PGPORT} dbname={PGDATABASE} user={PGUSER} password={PGPASSWORD}"

SQLSTATE_MAP = {
    '23505': "Нарушение уникальности.",
    '23502': "Обязательное поле не заполнено.",
    '23514': "Нарушено ограничение CHECK.",
    '23503': "Нарушение внешнего ключа.",
    '22P02': "Неверный формат данных.",
}

def sqlstate_message(exc: Exception) -> str:
    code = getattr(exc, 'pgcode', None)
    if code and code in SQLSTATE_MAP:
        return SQLSTATE_MAP[code]
    return str(exc)

def _resolve_sql_path(filename: str) -> Path:
    """
    Ищем SQL рядом с модулем
    """
    name = filename.strip()
    candidates = [
        Path(name),
        Path.cwd() / name,
        Path(__file__).resolve().parent / name,
        Path(__file__).resolve().parent.parent / name,
        Path(__file__).resolve().parent / "src" / name,
        Path(__file__).resolve().parent.parent / "src" / name,
        Path(__file__).resolve().parent / "sql" / name,
        Path(__file__).resolve().parent.parent / "sql" / name,
    ]
    for c in candidates:
        if c.is_file():
            return c
    raise FileNotFoundError(f"SQL file not found: {filename} (cwd={Path.cwd()}, module_dir={Path(__file__).resolve().parent})")

# -------------------- Conn --------------------
@contextmanager
def get_conn():
    try:
        if logger.isEnabledFor(logging.DEBUG) or DB_LOG_CONN:
            logger.debug("DB connect attempt host=%s port=%s db=%s user=%s", PGHOST, PGPORT, PGDATABASE, PGUSER)
        conn = psycopg2.connect(DSN)
        if logger.isEnabledFor(logging.DEBUG) or DB_LOG_CONN:
            logger.debug("DB connect OK")
    except Exception as e:
        logger.error("DB connect ERROR: %s", sqlstate_message(e))
        raise
    try:
        conn.set_client_encoding('UTF8')
        yield conn
    finally:
        try:
            conn.close()
            if logger.isEnabledFor(logging.DEBUG) or DB_LOG_CONN:
                logger.debug("DB connection closed")
        except Exception:
            pass

def table_exists(schema: str, table: str) -> bool:
    sql = """
    SELECT 1
    FROM information_schema.tables
    WHERE table_schema=%s AND table_name=%s
    """
    with get_conn() as conn:
        with conn.cursor() as cur:
            cur.execute(sql, (schema, table))
            return cur.fetchone() is not None

# НЕУЯЗВИМОЕ БАГОПРОТИВЯЩЕЕСЯ ОШИБКОНЕВОЗМОЖНОЕ извлечение SQL
_DOLLAR_TAG = re.compile(r"\$[A-Za-z0-9_]*\$")

def _split_sql(sql_text: str):
    stmts, buf = [], []
    i, n = 0, len(sql_text)
    in_s, in_d = False, False
    line_cmt = False
    block_cmt = 0
    dollar = None
    while i < n:
        ch = sql_text[i]
        ch2 = sql_text[i+1] if i+1 < n else ''

        if line_cmt:
            buf.append(ch)
            if ch == '\n': line_cmt = False
            i += 1; continue
        if block_cmt:
            buf.append(ch)
            if ch == '*' and ch2 == '/':
                buf.append(ch2); block_cmt -= 1; i += 2
            else:
                i += 1
            continue
        if dollar:
            buf.append(ch)
            if ch == '$' and sql_text.startswith(dollar, i):
                buf.extend(list(dollar[1:])); i += len(dollar); dollar = None
            else:
                i += 1
            continue

        if ch == '-' and ch2 == '-' and not in_s and not in_d:
            buf.append(ch); buf.append(ch2); line_cmt = True; i += 2; continue
        if ch == '/' and ch2 == '*' and not in_s and not in_d:
            buf.append(ch); buf.append(ch2); block_cmt += 1; i += 2; continue

        if ch == "'" and not in_d: in_s = not in_s; buf.append(ch); i += 1; continue
        if ch == '"' and not in_s: in_d = not in_d; buf.append(ch); i += 1; continue

        if ch == '$' and not in_s and not in_d:
            m = _DOLLAR_TAG.match(sql_text, i)
            if m:
                tag = m.group(0)
                dollar = tag
                buf.append(tag)
                i += len(tag)
                continue

        if ch == ';' and not in_s and not in_d:
            stmt = ''.join(buf).strip()
            if stmt:
                stmts.append(stmt)
            buf = []
            i += 1
            continue

        buf.append(ch); i += 1

    tail = ''.join(buf).strip()
    if tail: stmts.append(tail)
    return stmts

def exec_sql_file(path: str) -> int:
    p = _resolve_sql_path(path)
    if not p.is_file():
        raise FileNotFoundError(f"SQL file not found: {path}")

    b = p.read_bytes().replace(b"\xC2\xA0", b" ")
    try:
        sql_text = b.decode("utf-8-sig")
    except UnicodeDecodeError as e:
        bad_pos = e.start
        ctx = b[max(0, bad_pos-12):bad_pos+12]
        raise UnicodeDecodeError(
            f"SQL not in UTF-8. Bad byte {hex(b[bad_pos])} at {bad_pos}. Context: {ctx}"
        )
    sql_text = sql_text.replace('\u00A0', ' ')
    statements = _split_sql(sql_text)

    executed = 0
    with get_conn() as conn:
        try:
            with conn.cursor() as cur:
                for s in statements:
                    st = s.strip()
                    if not st or st.startswith('\\'):
                        continue
                    preview = " ".join(st.split())[:180]
                    logger.info("DDL/DML: %s", preview)
                    cur.execute(st)
                    executed += 1
            conn.commit()
            logger.info("Executed %d statements from %s", executed, str(p))
        except Exception as e:
            conn.rollback()
            logger.error("exec_sql_file ERROR: %s", sqlstate_message(e))
            logger.exception("exec_sql_file stack")
            raise Exception(sqlstate_message(e)) from e
    return executed

def drop_schema(schema: str = "app"):
    with get_conn() as conn:
        with conn.cursor() as cur:
            logger.info("DDL: DROP SCHEMA IF EXISTS %s CASCADE", schema)
            cur.execute(f"DROP SCHEMA IF EXISTS {schema} CASCADE;")
        conn.commit()

def create_schema(ddl_path: str = "ddl.sql", demo_path: str | None = "demo_data.sql"):
    logger.info("Create schema start: ddl=%s demo=%s", ddl_path, demo_path)
    ddl_real = _resolve_sql_path(ddl_path)
    executed = exec_sql_file(str(ddl_real))
    if demo_path:
        try:
            demo_real = _resolve_sql_path(demo_path)
            exec_sql_file(str(demo_real))
        except FileNotFoundError:
            logger.warning("demo data file not found: %s", demo_path)
        except Exception as e:
            logger.warning("demo_data.sql error: %s", e)
    logger.info("Create schema done: statements=%d", executed)
    return executed

# Пользователи
def register_user(login: str, password: str):
    sql = """
    INSERT INTO app.app_user (login, password_hash, is_admin)
    VALUES (%s, ext.crypt(%s, ext.gen_salt('bf')), FALSE)
    RETURNING id, login, is_admin, created_at;
    """
    with get_conn() as conn:
        with conn.cursor() as cur:
            logger.info("DML: register_user login=%s", login)
            cur.execute(sql, (login, password))
            row = cur.fetchone()
        conn.commit()
    return {"id": row[0], "login": row[1], "is_admin": row[2], "created_at": row[3]}

def authenticate(login: str, password: str):
    admin_login = os.getenv("ADMIN_LOGIN")
    admin_password = os.getenv("ADMIN_PASSWORD")

    if not table_exists("app", "app_user"):
        if admin_login and admin_password and login == admin_login and password == admin_password:
            logger.info("AUTH ephemeral admin via .env")
            return {"id": 0, "login": admin_login, "is_admin": True, "created_at": None, "ephemeral": True}
        return None

    sql = """
    SELECT id, login, is_admin, created_at
    FROM app.app_user
    WHERE login = %s
      AND password_hash = ext.crypt(%s, password_hash)
    """
    with get_conn() as conn:
        with conn.cursor() as cur:
            cur.execute(sql, (login, password))
            row = cur.fetchone()
    if row:
        return {"id": row[0], "login": row[1], "is_admin": row[2], "created_at": row[3], "ephemeral": False}

    if admin_login and admin_password and login == admin_login and password == admin_password:
        logger.info("AUTH ephemeral admin via .env")
        return {"id": 0, "login": admin_login, "is_admin": True, "created_at": None, "ephemeral": True}
    return None

def ensure_admin_from_env():
    admin_login = os.getenv("ADMIN_LOGIN")
    admin_password = os.getenv("ADMIN_PASSWORD")
    if not admin_login or not admin_password:
        logger.error("ensure_admin_from_env: ADMIN_LOGIN/PASSWORD not set")
        return None
    if not table_exists("app", "app_user"):
        logger.error("ensure_admin_from_env: schema not ready")
        return None

    sel = "SELECT id, is_admin, login, created_at FROM app.app_user WHERE login = %s"
    with get_conn() as conn:
        with conn.cursor() as cur:
            cur.execute(sel, (admin_login,))
            row = cur.fetchone()
            if row:
                user_id, is_admin, login, created_at = row
                if not is_admin:
                    cur.execute("UPDATE app.app_user SET is_admin=TRUE WHERE id=%s", (user_id,))
                    is_admin = True
                conn.commit()
                return {"id": user_id, "login": login, "is_admin": is_admin, "created_at": created_at, "ephemeral": False}

            ins = """
            INSERT INTO app.app_user (login, password_hash, is_admin)
            VALUES (%s, ext.crypt(%s, ext.gen_salt('bf')), TRUE)
            RETURNING id, login, is_admin, created_at
            """
            cur.execute(ins, (admin_login, admin_password))
            uid, login, is_admin, created_at = cur.fetchone()
        conn.commit()
    return {"id": uid, "login": login, "is_admin": is_admin, "created_at": created_at, "ephemeral": False}

def delete_user(user_id: int):
    sql = "DELETE FROM app.app_user WHERE id = %s"
    with get_conn() as conn:
        with conn.cursor() as cur:
            logger.info("DML: delete_user id=%s", user_id)
            cur.execute(sql, (user_id,))
        conn.commit()

# Домены
def add_domain(user_id: int, domain: str):
    sql_txt = """
    INSERT INTO app.tracked_domain (user_id, domain)
    VALUES (%s, %s)
    RETURNING id, submitted_at;
    """
    try:
        with get_conn() as conn:
            with conn.cursor() as cur:
                logger.info("DML: add_domain user_id=%s domain=%s", user_id, domain)
                cur.execute(sql_txt, (user_id, domain))
                row = cur.fetchone()
            conn.commit()
        return {"id": row[0], "submitted_at": row[1]}
    except Exception as e:
        logger.error("add_domain ERROR: %s", sqlstate_message(e))
        raise Exception(sqlstate_message(e)) from e

def delete_domain_by_name(user_id: int, domain: str):
    sql = "DELETE FROM app.tracked_domain WHERE user_id = %s AND lower(domain) = lower(%s)"
    with get_conn() as conn:
        with conn.cursor() as cur:
            logger.info("DML: delete_domain_by_name user_id=%s domain=%s", user_id, domain)
            cur.execute(sql, (user_id, domain))
        conn.commit()

def list_user_domains(user_id: int):
    sql = """
    SELECT domain, state, started_at, tracking_started
    FROM app.v_domain_current_state
    WHERE user_id = %s
    ORDER BY domain
    """
    with get_conn() as conn:
        with conn.cursor() as cur:
            cur.execute(sql, (user_id,))
            rows = cur.fetchall()
            cols = [d[0] for d in cur.description]
    return [dict(zip(cols, r)) for r in rows]

def list_tracked_domains():
    sql_txt = """
    SELECT id, user_id, domain, submitted_at
    FROM app.tracked_domain
    ORDER BY submitted_at ASC, id ASC
    """
    with get_conn() as conn:
        with conn.cursor() as cur:
            cur.execute(sql_txt)
            cols = [d[0] for d in cur.description]
            rows = cur.fetchall()
    return [dict(zip(cols, r)) for r in rows]

# Состояния и метрики
def get_current_state(domain_id: int):
    sql = """
        SELECT state::text, started_at
        FROM app.v_domain_current_state
        WHERE domain_id = %s
        LIMIT 1
    """
    with get_conn() as conn:
        with conn.cursor() as cur:
            cur.execute(sql, (domain_id,))
            row = cur.fetchone()
    if not row:
        return None
    return {"state": row[0], "started_at": row[1]}

def set_state(domain_id: int, new_state: str, ts: datetime | None = None, details: dict | None = None):
    if new_state not in ('active','ddos','downtime'):
        raise ValueError("Invalid state")
    now = ts or datetime.now(timezone.utc)
    with get_conn() as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT app.fn_set_domain_state(%s, %s::app.domain_state, %s, %s)",
                        (domain_id, new_state, now, Json(details or {})))
        conn.commit()
    return {"state": new_state, "started_at": now, "ended_at": None}

def insert_metric_sample(
    domain_id: int,
    ts: datetime,
    pps: int,
    uniq_ips: int,
    bytes_per_s: int,
    ok: bool,
    source: str,
    extra: dict | None = None,
    src_ips: list[str] | None = None,
):
    src_ips = src_ips or []
    sql_txt = """
    INSERT INTO app.metric_sample
      (domain_id, ts, packets_per_s, uniq_ips, bytes_per_s, ok, source, extra, src_ips)
    VALUES
      (%s,%s,%s,%s,%s,%s,%s,%s, %s::inet[])
    RETURNING id;
    """
    with get_conn() as conn:
        with conn.cursor() as cur:
            cur.execute(
                sql_txt,
                (domain_id, ts, pps, uniq_ips, bytes_per_s, ok, source, Json(extra or {}), src_ips)
            )
            row = cur.fetchone()
        conn.commit()
    return row[0]

# Топ сбоев
def list_top_failures(limit: int = 100):
    sql = """
    WITH agg AS (
        SELECT domain,
               COUNT(*)      AS ddos_count_hour,
               MAX(event_ts) AS last_ddos_ts
        FROM app.v_ddos_events_last_hour
        GROUP BY domain
    ),
    watchers AS (
        SELECT lower(domain) AS domain_lc, COUNT(*) AS watchers
        FROM app.tracked_domain
        GROUP BY lower(domain)
    )
    SELECT a.domain,
           a.ddos_count_hour,
           a.last_ddos_ts,
           COALESCE(w.watchers, 0) AS watchers
    FROM agg a
    LEFT JOIN watchers w ON lower(a.domain) = w.domain_lc
    ORDER BY a.ddos_count_hour DESC, a.last_ddos_ts DESC
    LIMIT %s
    """
    with get_conn() as conn:
        with conn.cursor() as cur:
            cur.execute(sql, (limit,))
            rows = cur.fetchall()
            cols = [d[0] for d in cur.description]
    return [dict(zip(cols, r)) for r in rows]

# Утилиты SQL
def run_select(sql: str, params: tuple | list = ()):
    #Безопасный SELECT. Возвращает (columns, rows).
    with get_conn() as conn:
        with conn.cursor() as cur:
            if DB_LOG_SQL_PREVIEW:
                preview = " ".join(sql.split())[:180]
                logger.info("SELECT: %s params=%s", preview, params)
            cur.execute(sql, params)
            cols = [d.name for d in cur.description]
            rows = cur.fetchall()
    return cols, rows

def exec_txn(sql_statements: list[tuple[str, tuple]]):
    #Выполнить пачку операторов в одной транзакции: [(sql, params), ...]
    with get_conn() as conn:
        with conn.cursor() as cur:
            for sql, params in sql_statements:
                if DB_LOG_SQL_PREVIEW:
                    preview = " ".join(sql.split())[:180]
                    logger.info("TXN: %s params=%s", preview, params)
                cur.execute(sql, params)
        conn.commit()

def list_tables(schema: str = "app"):
    sql = """
    SELECT table_schema, table_name
    FROM information_schema.tables
    WHERE table_schema=%s AND table_type='BASE TABLE'
    ORDER BY 1,2
    """
    return run_select(sql, (schema,))[1]

def list_columns(schema: str, table: str):
    sql = """
    SELECT column_name, data_type, udt_schema, udt_name, is_nullable, column_default, ordinal_position
    FROM information_schema.columns
    WHERE table_schema=%s AND table_name=%s
    ORDER BY ordinal_position
    """
    cols, rows = run_select(sql, (schema, table))
    return [dict(zip(cols, r)) for r in rows]

def preview(sql: str, limit: int = 200, params: tuple | list = ()): 
    s = sql.strip().rstrip(';')
    import re as _re
    if _re.search(r"\blimit\b\s+\d+", s, flags=_re.I) is None:
        s = s + " LIMIT " + str(limit)
    return run_select(s, params)

def is_column_protected(schema: str, table: str, column: str) -> bool:
    sql = """
      SELECT 1
      FROM app.protected_column
      WHERE schema_name=%s AND table_name=%s AND column_name=%s
    """
    with get_conn() as conn:
        with conn.cursor() as cur:
            cur.execute(sql, (schema, table, column))
            return cur.fetchone() is not None

def protect_column(schema: str, table: str, column: str, reason: str):
    sql = """
      INSERT INTO app.protected_column(schema_name, table_name, column_name, reason)
      VALUES (%s,%s,%s,%s)
      ON CONFLICT (schema_name, table_name, column_name)
      DO UPDATE SET reason = EXCLUDED.reason
    """
    with get_conn() as conn:
        with conn.cursor() as cur:
            cur.execute(sql, (schema, table, column, reason))
        conn.commit()

def list_constraint_names(schema: str, table: str) -> list[str]:
    sql = """
    SELECT con.conname
    FROM pg_constraint con
    JOIN pg_class rel ON rel.oid = con.conrelid
    JOIN pg_namespace n ON n.oid = rel.relnamespace
    WHERE n.nspname=%s AND rel.relname=%s
    ORDER BY con.conname
    """
    return [r[0] for r in run_select(sql, (schema, table))[1]]

def list_fk_pairs(schema: str, left_table: str, right_table: str) -> list[tuple[str,str]]:
    """Return list of (left_col, right_col) for FK between left/right tables."""
    sql = """
    SELECT a_left.attname AS left_col, a_right.attname AS right_col
    FROM pg_constraint c
    JOIN pg_class r_right ON r_right.oid = c.conrelid
    JOIN pg_namespace n_right ON n_right.oid = r_right.relnamespace
    JOIN pg_class r_left ON r_left.oid = c.confrelid
    JOIN pg_namespace n_left ON n_left.oid = r_left.relnamespace
    JOIN unnest(c.conkey) WITH ORDINALITY AS ck(attnum, ord) ON TRUE
    JOIN unnest(c.confkey) WITH ORDINALITY AS fk(attnum, ord) ON fk.ord = ck.ord
    JOIN pg_attribute a_right ON a_right.attrelid = r_right.oid AND a_right.attnum = ck.attnum
    JOIN pg_attribute a_left  ON a_left.attrelid  = r_left.oid  AND a_left.attnum  = fk.attnum
    WHERE c.contype = 'f'
      AND n_left.nspname = %s AND r_left.relname = %s
      AND n_right.nspname = %s AND r_right.relname = %s
    UNION
    SELECT a_left.attname AS left_col, a_right.attname AS right_col
    FROM pg_constraint c
    JOIN pg_class r_left ON r_left.oid = c.conrelid
    JOIN pg_namespace n_left ON n_left.oid = r_left.relnamespace
    JOIN pg_class r_right ON r_right.oid = c.confrelid
    JOIN pg_namespace n_right ON n_right.oid = r_right.relnamespace
    JOIN unnest(c.conkey) WITH ORDINALITY AS ck(attnum, ord) ON TRUE
    JOIN unnest(c.confkey) WITH ORDINALITY AS fk(attnum, ord) ON fk.ord = ck.ord
    JOIN pg_attribute a_left ON a_left.attrelid = r_left.oid AND a_left.attnum = ck.attnum
    JOIN pg_attribute a_right  ON a_right.attrelid  = r_right.oid  AND a_right.attnum  = fk.attnum
    WHERE c.contype = 'f'
      AND n_left.nspname = %s AND r_left.relname = %s
      AND n_right.nspname = %s AND r_right.relname = %s
    ORDER BY 1,2
    """
    cols, rows = run_select(sql, (schema, left_table, schema, right_table, schema, left_table, schema, right_table))
    return [(l, r) for l, r in rows]

# ==================== Представления (VIEW и MATERIALIZED VIEW) ====================
# Блок функций для работы с обычными представлениями (VIEW) и материализованными (MATERIALIZED VIEW)
# Все функции используют параметризованные запросы для безопасности

def list_views(schema: str = "app", materialized: bool = False):
    """
    Получить список представлений в указанной схеме.
    
    Для обычных VIEW использует information_schema.views (стандартный способ).
    Для MATERIALIZED VIEW использует pg_class, т.к. они хранятся как таблицы (relkind='m').
    
    Args:
        schema: имя схемы БД (по умолчанию "app")
        materialized: если True - возвращает MATERIALIZED VIEW, иначе обычные VIEW
    
    Returns:
        Список словарей с информацией о представлениях:
        - view_name: имя представления
        - size: размер в читаемом формате (только для MATERIALIZED VIEW)
        - comment: комментарий к представлению (если есть)
    """
    if materialized:
        # Запрос для MATERIALIZED VIEW через системные таблицы PostgreSQL
        # pg_class содержит информацию о всех объектах БД (таблицы, индексы, VIEW и т.д.)
        # relkind='m' означает материализованное представление
        # pg_total_relation_size возвращает размер включая индексы
        # pg_size_pretty форматирует размер в читаемый вид (KB, MB, GB)
        sql = """
        SELECT c.relname AS view_name,
               pg_size_pretty(pg_total_relation_size(c.oid)) AS size,
               obj_description(c.oid, 'pg_class') AS comment
        FROM pg_class c
        JOIN pg_namespace n ON n.oid = c.relnamespace
        WHERE n.nspname = %s
          AND c.relkind = 'm'  -- 'm' = materialized view
        ORDER BY c.relname
        """
    else:
        # Запрос для обычных VIEW через стандартный information_schema
        # information_schema.views содержит только обычные VIEW, не материализованные
        sql = """
        SELECT table_name AS view_name,
               NULL AS size,
               NULL AS comment
        FROM information_schema.views
        WHERE table_schema = %s
        ORDER BY table_name
        """
    # Выполняем запрос и преобразуем результат в список словарей
    cols, rows = run_select(sql, (schema,))
    return [dict(zip(cols, r)) for r in rows]

def list_all_views(schema: str = "app"):
    """
    Получить объединенный список всех представлений (обычных и материализованных).
    
    Удобная функция для отображения всех представлений в одном списке с пометкой типа.
    
    Args:
        schema: имя схемы БД (по умолчанию "app")
    
    Returns:
        Список словарей со всеми представлениями, каждый содержит:
        - view_name: имя представления
        - is_materialized: True для MATERIALIZED VIEW, False для обычных
        - size: размер (только для MATERIALIZED VIEW)
        - comment: комментарий (если есть)
    """
    # Получаем отдельно обычные и материализованные представления
    regular = list_views(schema, materialized=False)
    materialized = list_views(schema, materialized=True)
    
    # Добавляем флаг типа для каждого представления
    # Это позволяет в GUI различать типы представлений
    for v in regular:
        v['is_materialized'] = False
    for v in materialized:
        v['is_materialized'] = True
    
    # Объединяем списки и возвращаем
    return regular + materialized

def get_view_definition(schema: str, view_name: str, materialized: bool = False):
    """
    Получить SQL определение (исходный запрос) представления.
    
    Для обычных VIEW используется information_schema.views.view_definition.
    Для MATERIALIZED VIEW используется функция pg_get_viewdef().
    
    Args:
        schema: имя схемы БД
        view_name: имя представления
        materialized: True для MATERIALIZED VIEW, False для обычного VIEW
    
    Returns:
        Строка с SQL определением представления или None, если не найдено
    """
    if materialized:
        # Для MATERIALIZED VIEW используем функцию pg_get_viewdef()
        # regclass - это тип PostgreSQL для идентификаторов объектов БД
        # true - означает "красивое форматирование" (с отступами)
        sql = """
        SELECT pg_get_viewdef(%s::regclass, true) AS definition
        """
        # Формируем полное имя объекта (схема.имя) для regclass
        view_qualified = f"{schema}.{view_name}"
        # Используем прямой вызов, т.к. pg_get_viewdef требует специальный синтаксис
        with get_conn() as conn:
            with conn.cursor() as cur:
                cur.execute(sql, (view_qualified,))
                row = cur.fetchone()
        if row:
            return row[0]
        return None
    else:
        # Для обычных VIEW используем стандартный information_schema
        sql = """
        SELECT view_definition AS definition
        FROM information_schema.views
        WHERE table_schema = %s AND table_name = %s
        """
        cols, rows = run_select(sql, (schema, view_name))
        if rows:
            return rows[0][0]
        return None

def create_view(schema: str, view_name: str, definition: str, materialized: bool = False, with_data: bool = True):
    """
    Создать новое представление (обычное или материализованное).
    
    Выполняет DDL операцию CREATE VIEW или CREATE MATERIALIZED VIEW.
    Валидирует имя представления на безопасность (только буквы, цифры, подчеркивания).
    
    Args:
        schema: имя схемы БД
        view_name: имя представления (валидируется)
        definition: SQL запрос SELECT, который определяет представление
        materialized: True для MATERIALIZED VIEW, False для обычного VIEW
        with_data: для MATERIALIZED VIEW - загружать данные сразу (True) или создать пустым (False)
    
    Raises:
        ValueError: если имя представления содержит недопустимые символы
        Exception: если SQL определение некорректно или представление уже существует
    """
    # Валидация имени представления для безопасности
    # Разрешаем только буквы (латиница), цифры и подчеркивания
    # Имя должно начинаться с буквы или подчеркивания
    if not re.match(r'^[a-zA-Z_][a-zA-Z0-9_]*$', view_name):
        raise ValueError(f"Некорректное имя представления: {view_name}")
    
    # Определяем тип создаваемого объекта
    view_type = "MATERIALIZED VIEW" if materialized else "VIEW"
    
    # Для MATERIALIZED VIEW можно указать WITH DATA или WITH NO DATA
    # WITH DATA - сразу загружает данные (по умолчанию)
    # WITH NO DATA - создает пустое представление (данные загрузятся при первом REFRESH)
    data_clause = ""
    if materialized:
        data_clause = "WITH DATA" if with_data else "WITH NO DATA"
    
    # Формируем SQL команду создания представления
    # ВАЖНО: definition не экранируется, т.к. это SQL код, который должен быть валидным
    # Валидация definition должна выполняться на уровне GUI или через EXPLAIN
    sql = f"CREATE {view_type} {schema}.{view_name} AS {definition} {data_clause}"
    
    # Выполняем DDL операцию в транзакции
    with get_conn() as conn:
        with conn.cursor() as cur:
            # Логируем операцию, если включено логирование SQL
            if DB_LOG_SQL_PREVIEW:
                preview = " ".join(sql.split())[:180]
                logger.info("DDL: CREATE %s %s.%s", view_type, schema, view_name)
            # Выполняем создание представления
            cur.execute(sql)
        # Коммитим транзакцию
        conn.commit()
    # Логируем успешное создание
    logger.info("Created %s %s.%s", view_type, schema, view_name)

def drop_view(schema: str, view_name: str, materialized: bool = False, cascade: bool = False):
    """
    Удалить представление из базы данных.
    
    Использует IF EXISTS для безопасного удаления (не вызовет ошибку, если представления нет).
    CASCADE удаляет зависимые объекты (например, другие VIEW, которые используют это представление).
    
    Args:
        schema: имя схемы БД
        view_name: имя представления для удаления
        materialized: True для MATERIALIZED VIEW, False для обычного VIEW
        cascade: если True, удаляет зависимые объекты автоматически
    """
    # Определяем тип удаляемого объекта
    view_type = "MATERIALIZED VIEW" if materialized else "VIEW"
    
    # CASCADE удаляет все объекты, зависящие от этого представления
    # Без CASCADE удаление не удастся, если есть зависимости
    cascade_clause = "CASCADE" if cascade else ""
    
    # Формируем SQL команду удаления
    # IF EXISTS предотвращает ошибку, если представление уже удалено
    sql = f"DROP {view_type} IF EXISTS {schema}.{view_name} {cascade_clause}"
    
    # Выполняем DDL операцию
    with get_conn() as conn:
        with conn.cursor() as cur:
            # Логируем операцию
            if DB_LOG_SQL_PREVIEW:
                logger.info("DDL: DROP %s %s.%s", view_type, schema, view_name)
            cur.execute(sql)
        conn.commit()
    # Логируем успешное удаление
    logger.info("Dropped %s %s.%s", view_type, schema, view_name)

def refresh_materialized_view(schema: str, view_name: str, concurrently: bool = False):
    """
    Обновить данные в материализованном представлении.
    
    MATERIALIZED VIEW хранит данные физически, поэтому их нужно периодически обновлять.
    Обычный REFRESH блокирует представление на время обновления.
    CONCURRENTLY позволяет читать данные во время обновления, но требует уникальный индекс.
    
    Args:
        schema: имя схемы БД
        view_name: имя MATERIALIZED VIEW для обновления
        concurrently: если True, использует CONCURRENTLY (не блокирует чтение, но медленнее)
    
    Raises:
        Exception: если CONCURRENTLY используется без уникального индекса или представление не найдено
    """
    # CONCURRENTLY позволяет читать данные во время обновления
    # Но требует наличие хотя бы одного уникального индекса на представлении
    concurrently_clause = "CONCURRENTLY" if concurrently else ""
    
    # Формируем SQL команду обновления
    sql = f"REFRESH MATERIALIZED VIEW {concurrently_clause} {schema}.{view_name}"
    
    # Выполняем обновление
    with get_conn() as conn:
        with conn.cursor() as cur:
            if DB_LOG_SQL_PREVIEW:
                logger.info("DDL: REFRESH MATERIALIZED VIEW %s %s.%s", concurrently_clause, schema, view_name)
            try:
                cur.execute(sql)
            except Exception as e:
                # Обрабатываем специфичную ошибку CONCURRENTLY
                # Если используется CONCURRENTLY без индекса, PostgreSQL вернет понятную ошибку
                if concurrently and 'concurrently' in str(e).lower():
                    raise Exception("CONCURRENTLY refresh требует уникальный индекс на материализованном представлении") from e
                # Пробрасываем другие ошибки дальше
                raise
        conn.commit()
    # Логируем успешное обновление
    logger.info("Refreshed MATERIALIZED VIEW %s.%s", schema, view_name)

def view_exists(schema: str, view_name: str, materialized: bool = False) -> bool:
    """
    Проверить, существует ли представление в базе данных.
    
    Используется для валидации перед операциями создания/удаления.
    
    Args:
        schema: имя схемы БД
        view_name: имя представления для проверки
        materialized: True для MATERIALIZED VIEW, False для обычного VIEW
    
    Returns:
        True если представление существует, False иначе
    """
    if materialized:
        # Для MATERIALIZED VIEW проверяем через pg_class
        # relkind='m' означает материализованное представление
        sql = """
        SELECT 1
        FROM pg_class c
        JOIN pg_namespace n ON n.oid = c.relnamespace
        WHERE n.nspname = %s
          AND c.relname = %s
          AND c.relkind = 'm'
        """
    else:
        # Для обычных VIEW используем information_schema
        sql = """
        SELECT 1
        FROM information_schema.views
        WHERE table_schema = %s AND table_name = %s
        """
    # Выполняем запрос и проверяем наличие результата
    with get_conn() as conn:
        with conn.cursor() as cur:
            cur.execute(sql, (schema, view_name))
            # Если fetchone() вернул строку - представление существует
            return cur.fetchone() is not None

def get_materialized_view_info(schema: str, view_name: str):
    """
    Получить детальную информацию о материализованном представлении.
    
    Возвращает размеры, комментарии и количество индексов для отображения в GUI.
    
    Args:
        schema: имя схемы БД
        view_name: имя MATERIALIZED VIEW
    
    Returns:
        Словарь с информацией:
        - view_name: имя представления
        - total_size: общий размер (данные + индексы) в читаемом формате
        - table_size: размер только данных (без индексов) в читаемом формате
        - comment: комментарий к представлению (если есть)
        - index_count: количество индексов на представлении
        Или None, если представление не найдено
    """
    # Запрос собирает информацию из системных таблиц PostgreSQL
    # pg_total_relation_size - размер включая индексы и TOAST
    # pg_relation_size - размер только таблицы данных
    # pg_size_pretty - форматирует байты в читаемый вид (KB, MB, GB)
    # obj_description - получает комментарий к объекту
    # Подзапрос считает количество индексов для CONCURRENTLY refresh
    sql = """
    SELECT 
        c.relname AS view_name,
        pg_size_pretty(pg_total_relation_size(c.oid)) AS total_size,
        pg_size_pretty(pg_relation_size(c.oid)) AS table_size,
        obj_description(c.oid, 'pg_class') AS comment,
        (SELECT COUNT(*) FROM pg_indexes WHERE schemaname = %s AND tablename = %s) AS index_count
    FROM pg_class c
    JOIN pg_namespace n ON n.oid = c.relnamespace
    WHERE n.nspname = %s
      AND c.relname = %s
      AND c.relkind = 'm'  -- 'm' = materialized view
    """
    # Выполняем запрос с параметрами (schema, view_name используются дважды)
    cols, rows = run_select(sql, (schema, view_name, schema, view_name))
    if rows:
        # Преобразуем результат в словарь для удобства использования
        return dict(zip(cols, rows[0]))
    return None