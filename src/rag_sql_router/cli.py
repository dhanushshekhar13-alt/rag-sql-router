import argparse

from . import db
from .agent import RouterAgent
from .rag import DocumentStore


def setup() -> None:
    path = db.seed()
    print(f"Seeded database at {path}")
    n = DocumentStore().index_directory()
    print(f"Indexed {n} document chunks")


def ask(question: str) -> None:
    result = RouterAgent(DocumentStore()).ask(question)
    print(f"\n[route: {result.route}]")
    if result.sql:
        print(f"SQL: {result.sql}")
    if result.error and not result.rows:
        print(f"SQL error: {result.error}")
    print(f"\n{result.answer}")
    for h in result.sources:
        print(f"  source: {h.source}")


def main() -> None:
    parser = argparse.ArgumentParser(prog="rag-sql-router")
    sub = parser.add_subparsers(dest="cmd", required=True)
    sub.add_parser("setup", help="Seed the sample database and index the documents")
    p_ask = sub.add_parser("ask", help="Ask a question")
    p_ask.add_argument("question")
    args = parser.parse_args()
    setup() if args.cmd == "setup" else ask(args.question)


if __name__ == "__main__":
    main()
