import re

FORBIDDEN = re.compile(
    r"\b(insert|update|delete|drop|alter|create|replace|truncate|attach|detach|pragma|vacuum|reindex)\b",
    re.IGNORECASE,
)


class UnsafeSQL(ValueError):
    pass


def extract_sql(text: str) -> str:
    """Pull SQL out of an LLM reply that may be wrapped in a code fence."""
    match = re.search(r"```(?:sql)?\s*(.*?)```", text, re.DOTALL | re.IGNORECASE)
    return (match.group(1) if match else text).strip()


def validate_select(sql: str) -> str:
    """Return the cleaned query if it is a single read-only SELECT, else raise."""
    cleaned = re.sub(r"--.*?$|/\*.*?\*/", "", sql, flags=re.MULTILINE | re.DOTALL).strip()
    cleaned = cleaned.rstrip(";").strip()
    if not cleaned:
        raise UnsafeSQL("Empty query")
    if ";" in cleaned:
        raise UnsafeSQL("Multiple statements are not allowed")
    if not re.match(r"^(select|with)\b", cleaned, re.IGNORECASE):
        raise UnsafeSQL("Only SELECT queries are allowed")
    if FORBIDDEN.search(cleaned):
        raise UnsafeSQL("Query contains a forbidden keyword")
    return cleaned
