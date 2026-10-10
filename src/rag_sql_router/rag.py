import uuid
from dataclasses import dataclass
from pathlib import Path

from fastembed import TextEmbedding
from qdrant_client import QdrantClient, models

from .config import settings


@dataclass
class Hit:
    text: str
    source: str
    score: float


def split_text(text: str, size: int, overlap: int) -> list[str]:
    if overlap >= size:
        raise ValueError("overlap must be smaller than chunk size")
    text = " ".join(text.split())
    chunks, start = [], 0
    while start < len(text):
        end = min(start + size, len(text))
        if end < len(text):
            cut = max(text.rfind(". ", start, end), text.rfind(" ", start, end))
            if cut > start + size // 2:
                end = cut + 1
        chunks.append(text[start:end].strip())
        if end >= len(text):
            break
        start = end - overlap
    return [c for c in chunks if c]


class DocumentStore:
    def __init__(self, path: str | None = None):
        self.client = QdrantClient(path=path or settings.qdrant_path)
        self.embedder = TextEmbedding(model_name=settings.embed_model)
        dim = len(next(iter(self.embedder.embed(["probe"]))))
        if not self.client.collection_exists(settings.collection):
            self.client.create_collection(
                settings.collection,
                vectors_config=models.VectorParams(size=dim, distance=models.Distance.COSINE),
            )

    def index_directory(self, directory: str | None = None) -> int:
        folder = Path(directory or settings.docs_dir)
        texts, payloads = [], []
        for f in sorted(folder.glob("*.md")) + sorted(folder.glob("*.txt")):
            for piece in split_text(f.read_text(encoding="utf-8"), settings.chunk_size, settings.chunk_overlap):
                texts.append(piece)
                payloads.append({"text": piece, "source": f.name})
        if not texts:
            return 0
        vectors = list(self.embedder.embed(texts))
        self.client.upsert(
            settings.collection,
            points=[
                models.PointStruct(id=str(uuid.uuid4()), vector=v.tolist(), payload=p)
                for v, p in zip(vectors, payloads)
            ],
        )
        return len(texts)

    def count(self) -> int:
        return self.client.count(settings.collection).count

    def search(self, query: str, k: int | None = None) -> list[Hit]:
        vector = next(iter(self.embedder.embed([query]))).tolist()
        res = self.client.query_points(settings.collection, query=vector, limit=k or settings.top_k)
        return [Hit(p.payload["text"], p.payload["source"], p.score) for p in res.points]
