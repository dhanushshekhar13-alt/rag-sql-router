import re
from typing import Callable

ROUTES = ("sql", "rag", "both")

ROUTER_PROMPT = (
    "You route user questions. Reply with exactly one word.\n"
    "- sql: needs numbers or records from the company database "
    "(employees, products, orders, sales, salaries, counts, totals).\n"
    "- rag: needs policy or rule text from documents (leave, refunds, returns, procedures).\n"
    "- both: needs facts from the database AND policy text.\n"
    "Answer with one of: sql, rag, both."
)

SQL_HINTS = re.compile(
    r"\b(how many|total|average|sum|count|highest|lowest|top|most|list|salary|salaries|orders?|sales|revenue|employees?|products?)\b",
    re.IGNORECASE,
)
RAG_HINTS = re.compile(
    r"\b(policy|policies|rule|rules|allowed|eligible|refund|return|leave|procedure|approval|window|carry)\b",
    re.IGNORECASE,
)


def heuristic_route(question: str) -> str:
    sql, rag = bool(SQL_HINTS.search(question)), bool(RAG_HINTS.search(question))
    if sql and rag:
        return "both"
    return "rag" if rag and not sql else "sql" if sql else "rag"


def route_question(question: str, llm: Callable[[str, str], str]) -> str:
    try:
        reply = llm(ROUTER_PROMPT, question).strip().lower()
    except Exception:
        return heuristic_route(question)
    for word in re.findall(r"[a-z]+", reply):
        if word in ROUTES:
            return word
    return heuristic_route(question)
