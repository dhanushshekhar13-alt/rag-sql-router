import sqlite3
from pathlib import Path

from .config import settings
from .sql_guard import validate_select

SCHEMA = """
CREATE TABLE employees (
    id INTEGER PRIMARY KEY, name TEXT, department TEXT, salary INTEGER, hire_date TEXT
);
CREATE TABLE products (
    id INTEGER PRIMARY KEY, name TEXT, category TEXT, price REAL
);
CREATE TABLE orders (
    id INTEGER PRIMARY KEY, product_id INTEGER, employee_id INTEGER,
    quantity INTEGER, order_date TEXT, region TEXT,
    FOREIGN KEY (product_id) REFERENCES products(id),
    FOREIGN KEY (employee_id) REFERENCES employees(id)
);
"""

EMPLOYEES = [
    (1, "Asha Rao", "Sales", 72000, "2021-03-15"),
    (2, "Vikram Singh", "Sales", 68000, "2022-07-01"),
    (3, "Meera Iyer", "Engineering", 95000, "2020-01-20"),
    (4, "Rohan Das", "Engineering", 88000, "2023-02-10"),
    (5, "Neha Gupta", "HR", 61000, "2019-11-05"),
]
PRODUCTS = [
    (1, "Laptop Pro", "Electronics", 1200.0),
    (2, "Wireless Mouse", "Accessories", 25.0),
    (3, "Standing Desk", "Furniture", 450.0),
    (4, "Monitor 27in", "Electronics", 320.0),
]
ORDERS = [
    (1, 1, 1, 5, "2025-01-10", "North"),
    (2, 2, 2, 40, "2025-01-18", "South"),
    (3, 3, 1, 8, "2025-02-02", "North"),
    (4, 4, 2, 12, "2025-02-14", "West"),
    (5, 1, 2, 3, "2025-03-05", "South"),
    (6, 2, 1, 25, "2025-03-22", "North"),
]


def seed(path: str | None = None) -> str:
    db_path = Path(path or settings.db_path)
    db_path.parent.mkdir(parents=True, exist_ok=True)
    if db_path.exists():
        db_path.unlink()
    with sqlite3.connect(db_path) as conn:
        conn.executescript(SCHEMA)
        conn.executemany("INSERT INTO employees VALUES (?,?,?,?,?)", EMPLOYEES)
        conn.executemany("INSERT INTO products VALUES (?,?,?,?)", PRODUCTS)
        conn.executemany("INSERT INTO orders VALUES (?,?,?,?,?,?)", ORDERS)
    return str(db_path)


def _connect(path: str | None = None) -> sqlite3.Connection:
    # Read-only connection: a second line of defence behind sql_guard.
    uri = f"file:{Path(path or settings.db_path).resolve()}?mode=ro"
    return sqlite3.connect(uri, uri=True)


def get_schema(path: str | None = None) -> str:
    with _connect(path) as conn:
        rows = conn.execute(
            "SELECT sql FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%'"
        ).fetchall()
    return "\n".join(r[0].strip() + ";" for r in rows)


def run_query(sql: str, path: str | None = None) -> tuple[list[str], list[tuple]]:
    safe = validate_select(sql)
    with _connect(path) as conn:
        cur = conn.execute(safe)
        columns = [d[0] for d in cur.description or []]
        rows = cur.fetchmany(settings.max_rows)
    return columns, rows
