import pytest

from rag_sql_router import db
from rag_sql_router.agent import RouterAgent
from rag_sql_router.rag import Hit


class FakeDocs:
    def count(self):
        return 1

    def search(self, query, k=None):
        return [Hit("Refunds within 30 days.", "refund_policy.md", 0.8)]


def make_llm(route, sql_replies):
    sql_iter = iter(sql_replies)

    def llm(system, user):
        if system.startswith("You route"):
            return route
        if system.startswith("You write SQLite"):
            return next(sql_iter)
        return "final answer"

    return llm


@pytest.fixture
def db_path(tmp_path):
    return db.seed(str(tmp_path / "t.db"))


def test_sql_route_returns_rows(db_path):
    llm = make_llm("sql", ["SELECT COUNT(*) FROM orders"])
    res = RouterAgent(FakeDocs(), llm, db_path).ask("how many orders")
    assert res.route == "sql"
    assert res.rows == [(6,)]
    assert res.sources == []


def test_rag_route_uses_docs_only(db_path):
    res = RouterAgent(FakeDocs(), make_llm("rag", []), db_path).ask("refund policy")
    assert res.sql is None
    assert res.sources[0].source == "refund_policy.md"


def test_both_route_combines(db_path):
    llm = make_llm("both", ["SELECT COUNT(*) FROM employees"])
    res = RouterAgent(FakeDocs(), llm, db_path).ask("q")
    assert res.rows == [(5,)] and res.sources


def test_unsafe_sql_is_blocked_then_retried(db_path):
    llm = make_llm("sql", ["DROP TABLE orders", "SELECT COUNT(*) FROM orders"])
    res = RouterAgent(FakeDocs(), llm, db_path).ask("q")
    assert res.rows == [(6,)]
    assert db.run_query("SELECT COUNT(*) FROM orders", db_path)[1] == [(6,)]


def test_gives_up_after_two_bad_queries(db_path):
    llm = make_llm("sql", ["DELETE FROM orders", "DROP TABLE orders"])
    res = RouterAgent(None, llm, db_path).ask("q")
    assert "could not find" in res.answer.lower()
    assert res.error
