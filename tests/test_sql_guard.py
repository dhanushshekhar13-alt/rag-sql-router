import pytest

from rag_sql_router.sql_guard import UnsafeSQL, extract_sql, validate_select


def test_allows_plain_select():
    assert validate_select("SELECT * FROM orders;") == "SELECT * FROM orders"


def test_allows_cte():
    assert validate_select("WITH t AS (SELECT 1) SELECT * FROM t").startswith("WITH")


@pytest.mark.parametrize(
    "sql",
    [
        "DROP TABLE orders",
        "DELETE FROM orders",
        "UPDATE orders SET quantity = 0",
        "INSERT INTO orders VALUES (1,1,1,1,'x','y')",
        "SELECT 1; DROP TABLE orders",
        "SELECT * FROM orders; SELECT * FROM products",
        "PRAGMA table_info(orders)",
        "",
    ],
)
def test_rejects_unsafe(sql):
    with pytest.raises(UnsafeSQL):
        validate_select(sql)


def test_comment_cannot_hide_write():
    with pytest.raises(UnsafeSQL):
        validate_select("/* hi */ DELETE FROM orders")


def test_extract_sql_from_fence():
    assert extract_sql("Here:\n```sql\nSELECT 1\n```") == "SELECT 1"
    assert extract_sql("SELECT 2") == "SELECT 2"
