import os
from dataclasses import dataclass

from dotenv import load_dotenv

load_dotenv()


@dataclass(frozen=True)
class Settings:
    llm_model: str = os.getenv("LLM_MODEL", "llama3.2")
    embed_model: str = os.getenv("EMBED_MODEL", "BAAI/bge-small-en-v1.5")
    db_path: str = os.getenv("DB_PATH", "data/company.db")
    docs_dir: str = os.getenv("DOCS_DIR", "data/policies")
    qdrant_path: str = os.getenv("QDRANT_PATH", "qdrant_data")
    collection: str = os.getenv("COLLECTION", "policies")
    chunk_size: int = int(os.getenv("CHUNK_SIZE", "700"))
    chunk_overlap: int = int(os.getenv("CHUNK_OVERLAP", "120"))
    top_k: int = int(os.getenv("TOP_K", "3"))
    max_rows: int = int(os.getenv("MAX_ROWS", "50"))


settings = Settings()
