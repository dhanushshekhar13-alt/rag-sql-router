from rag_sql_router.router import heuristic_route, route_question


def test_llm_answer_used():
    assert route_question("q", lambda s, u: "sql") == "sql"
    assert route_question("q", lambda s, u: "Route: BOTH.") == "both"


def test_garbage_reply_falls_back_to_heuristic():
    assert route_question("what is the refund policy", lambda s, u: "banana") == "rag"


def test_llm_failure_falls_back():
    def boom(s, u):
        raise RuntimeError("ollama down")

    assert route_question("how many orders", boom) == "sql"


def test_heuristics():
    assert heuristic_route("total sales per region") == "sql"
    assert heuristic_route("what is the leave policy") == "rag"
    assert heuristic_route("how many orders and what is the refund policy") == "both"
    assert heuristic_route("hello there") == "rag"
