import os, re, sys
from pathlib import Path
import db

ROOT = Path(__file__).resolve().parent.parent 
DEFAULT_SCHEMA = os.getenv("DB_DEFAULT_SCHEMA", "app")

SQL_INSERT_RE = re.compile(
    r"INSERT\s+INTO\s+((?:(?P<sch>\w+)\.)?(?P<tbl>\w+))\s*\((?P<cols>[^)]*)\)",
    re.I | re.M
)
DOT_COL_RE = re.compile(r"(?:(?P<sch>\w+)\.)?(?P<tbl>\w+)\.(?P<col>\w+)")

def build_allowed_columns(schema: str) -> set[tuple[str, str, str]]:
    """
    Вайтлист столбцов, которые показываются в ALTER TABLE -> DROP COLUMN.
    Совпадает с источником данных для выпадашек: list_tables + list_columns.
    """
    allowed: set[tuple[str, str, str]] = set()
    try:
        for _, tbl in db.list_tables(schema):
            for c in db.list_columns(schema, tbl):
                allowed.add((schema, tbl, c["column_name"]))
    except Exception as e:
        print(f"[protect_scan] Не удалось получить список столбцов из БД: {e}", file=sys.stderr)
    return allowed

def fetch_pk_columns(schema: str) -> set[tuple[str, str, str]]:
    """
    Возвращает множ-во (schema, table, column) для всех первичных ключей (PK).
    """
    sql = """
    SELECT n.nspname AS schema_name,
           c.relname AS table_name,
           a.attname AS column_name
    FROM pg_constraint con
    JOIN pg_class c ON c.oid = con.conrelid
    JOIN pg_namespace n ON n.oid = c.relnamespace
    JOIN unnest(con.conkey) AS k(attnum) ON TRUE
    JOIN pg_attribute a ON a.attrelid = c.oid AND a.attnum = k.attnum
    WHERE con.contype = 'p' AND n.nspname = %s
    ORDER BY 1,2,3
    """
    try:
        cols, rows = db.run_select(sql, (schema,))
        return {(r[0], r[1], r[2]) for r in rows}
    except Exception as e:
        print(f"[protect_scan] Не удалось получить PK: {e}", file=sys.stderr)
        return set()

def is_protected(schema: str, table: str, column: str) -> bool:
    try:
        return hasattr(db, "is_column_protected") and db.is_column_protected(schema, table, column)
    except Exception:
        # Если не смогли проверить — считаем, что не защищён (ниже всё равно фильтруем allowed)
        return False

def protect(schema: str, table: str, column: str, reason: str, allowed: set[tuple[str,str,str]]):
    """
    Защищаем столбец, только если он есть в вайтлисте allowed
    (т.е. он показывается в выпадающем DROP COLUMN).
    """
    key = (schema, table, column)
    if key not in allowed:
        return
    if is_protected(schema, table, column):
        return
    try:
        db.protect_column(schema, table, column, reason)
        print(f"[protect_scan] protected {schema}.{table}.{column} — {reason}")
    except Exception as e:
        print(f"[protect_scan] ошибка защиты {schema}.{table}.{column}: {e}", file=sys.stderr)

def iter_files():
    """
    Сканируем проект (python + sql файлы), исключая venv/.git.
    """
    exts = {".py", ".sql"}
    for p in ROOT.rglob("*"):
        if p.suffix.lower() in exts and p.is_file() and "venv" not in p.parts and ".git" not in p.parts:
            yield p

def main():
    schema = DEFAULT_SCHEMA
    allowed = build_allowed_columns(schema)
    if not allowed:
        print("[protect_scan] Пустой вайтлист столбцов — ничего не защищаю.", file=sys.stderr)
        return

    # 1) Всегда защищаем PK — сюда попадут и стандартные id-колонки.
    pk_cols = fetch_pk_columns(schema)
    for (sch, tbl, col) in pk_cols:
        protect(sch, tbl, col, "auto: primary key", allowed)

    # 2) Дополнительно защищаем упомянутые в коде/SQL колонки (если они из allowed).
    for path in iter_files():
        try:
            text = path.read_text(encoding="utf-8", errors="ignore")
        except Exception as e:
            print(f"[protect_scan] не читается {path}: {e}", file=sys.stderr)
            continue

        # INSERT ... (col1, col2, ...)
        for m in SQL_INSERT_RE.finditer(text):
            sch = m.group("sch") or schema
            tbl = m.group("tbl")
            cols_raw = m.group("cols") or ""
            cols = [c.strip().strip('"') for c in cols_raw.split(",") if c.strip()]
            for col in cols:
                if re.fullmatch(r"\w+", col):
                    protect(sch, tbl, col, f"auto: referenced in INSERT at {path}", allowed)

        # Dot-нотация: table.column / schema.table.column
        for m in DOT_COL_RE.finditer(text):
            sch = m.group("sch") or schema
            tbl = m.group("tbl")
            col = m.group("col")
            protect(sch, tbl, col, f"auto: referenced in code at {path}", allowed)

if __name__ == "__main__":
    main()
