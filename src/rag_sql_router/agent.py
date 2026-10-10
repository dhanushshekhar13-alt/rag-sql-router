from dataclasses import dataclass, field
from typing import Callable

import ollama

from . import db
from .config import settings
from .rag import DocumentStore, Hit
from .router import route_question
from .sql_guard import UnsafeSQL, extract_sql, validate_select

SQL_PROMPT = (
    "You write SQLite queries. Given the schema, reply with ONE read-only SELECT "
    "query that answers the question. Output only the SQL.\n\nSchema:\n{schema}"
)
ANSWER_PROMPT = (
    "Answer the question using ONLY the context below. Be concise. "
    "If the context is insufficient, say so.\n\n{context}"
)


@dataclass
class Result:
    answer: str
    route: str
    sql: str | None = None
    columns: list[str] = field(default_factory=list)
    rows: list[tuple] = field(default_factory=list)
    sources: list[Hit] = field(default_factory=list)
    error: str | None = None


def default_llm(system: str, user: str) -> str:
    resp = ollama.chat(
        model=settings.llm_model,
        messages=[{"role": "system", "content": system}, {"role": "user", "content": user}],
    )
    return resp["message"]["content"]


def format_rows(columns: list[str], rows: list[tuple]) -> str:
    if not rows:
        return "(no rows)"
    lines = [" | ".join(columns)] + [" | ".join(str(v) for v in r) for r in rows]
    return "\n".join(lines)


class RouterAgent:
    def __init__(
        self,
        docs: DocumentStore | None = None,
        llm: Callable[[str, str], str] = default_llm,
        db_path: str | None = None,
    ):
        self.docs = docs
        self.llm = llm
        self.db_path = db_path

    def _run_sql(self, question: str, result: Result) -> str | None:
        schema = db.get_schema(self.db_path)
        prompt = SQL_PROMPT.format(schema=schema)
        user = question
        for _ in range(2):  # one retry, feeding the error back to the model
            sql = extract_sql(self.llm(prompt, user))
            try:
                validate_select(sql)
                columns, rows = db.run_query(sql, self.db_path)
            except (UnsafeSQL, Exception) as exc:
                result.sql, result.error = sql, str(exc)
                user = f"{question}\n\nYour previous query failed: {sql}\nError: {exc}\nFix it."
                continue
            result.sql, result.columns, result.rows, result.error = sql, columns, rows, None
            return f"Database result (SQL: {sql}):\n{format_rows(columns, rows)}"
        return None

    def _run_rag(self, question: str, result: Result) -> str | None:
        if self.docs is None or not self.docs.count():
            return None
        hits = self.docs.search(question)
        result.sources = hits
        return "Policy documents:\n" + "\n\n".join(f"({h.source}) {h.text}" for h in hits)

    def ask(self, question: str) -> Result:
        route = route_question(question, self.llm)
        result = Result(answer="", route=route)
        parts = []
        if route in ("sql", "both"):
            if (ctx := self._run_sql(question, result)) is not None:
                parts.append(ctx)
        if route in ("rag", "both"):
            if (ctx := self._run_rag(question, result)) is not None:
                parts.append(ctx)
        if not parts:
            result.answer = "I could not find an answer from the database or the documents."
            return result
        result.answer = self.llm(ANSWER_PROMPT.format(context="\n\n".join(parts)), question)
        return result
