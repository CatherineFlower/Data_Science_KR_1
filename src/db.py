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

# -------------------- НЕУЯЗВИМОЕ БАГОПРОТИВЯЩЕЕСЯ ОШИБКОНЕВОЗМОЖНОЕ извлечение SQL --------------------
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

# -------------------- Пользователи --------------------
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

# -------------------- Домены --------------------
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

# -------------------- Состояния и метрики --------------------
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

# -------------------- Топ сбоев --------------------
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
