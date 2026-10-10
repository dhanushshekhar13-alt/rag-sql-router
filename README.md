# RAG-SQL Router Agent

An agent that decides, per question, whether to answer from **documents (RAG)**, a **SQL database**, or **both**. Ask "total quantity ordered per region" and it queries the database; ask "what is the refund window for electronics" and it searches policy documents; ask a mixed question and it uses both.

## How it works

1. **Route**: an LLM classifies the question as `sql`, `rag` or `both`. If the reply is unusable or the LLM is down, keyword heuristics decide.
2. **SQL path**: the LLM writes a query from the live schema. `sql_guard` accepts only a single read-only `SELECT`/`WITH` (no writes, no multiple statements, comments stripped), and the database is opened in SQLite read-only mode as a second layer. On failure the error is fed back for one retry.
3. **RAG path**: policy documents are chunked, embedded with `fastembed`, stored in local Qdrant and searched.
4. **Answer**: the LLM answers only from the gathered context. The UI shows the route, the generated SQL, a results table and document sources.

## Setup

```bash
python3.11 -m venv .venv && source .venv/bin/activate
pip install -e ".[dev]"
cp .env.example .env
ollama pull llama3.2
python -m rag_sql_router.cli setup     # seeds data/company.db and indexes data/policies
```

## Usage

```bash
streamlit run app.py
python -m rag_sql_router.cli ask "Which region ordered the most items?"
python -m rag_sql_router.cli ask "What is the refund window for electronics?"
python -m rag_sql_router.cli ask "How many orders did Asha place, and what refund can sales reps approve?"
```

## Tests

```bash
pytest
```

Tests use a fake LLM, fake document store and a temporary database, so no models or network are needed.

## Use your own data

Point `DB_PATH` at any SQLite file and `DOCS_DIR` at a folder of `.md`/`.txt` files, then rerun `setup`'s indexing step.

## Ideas for extension

- Add schema descriptions and example queries to improve SQL accuracy
- Support Postgres/MySQL with a read-only role
- Evaluate routing accuracy on a labelled question set
