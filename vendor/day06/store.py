"""Persistent PostgreSQL/pgvector store with cosine search and JSON metadata filters."""
from typing import Any
import psycopg
from psycopg.types.json import Jsonb
from .models import Chunk


class PgVectorStore:
    def __init__(self, database_url: str, dimensions: int) -> None:
        if dimensions < 1:
            raise ValueError("dimensions must be positive")
        self.database_url, self.dimensions = database_url, dimensions

    def create_schema(self) -> None:
        with psycopg.connect(self.database_url) as conn:
            conn.execute("CREATE EXTENSION IF NOT EXISTS vector")
            conn.execute(f"""CREATE TABLE IF NOT EXISTS day6_chunks (
                strategy TEXT NOT NULL, chunk_id TEXT NOT NULL, document_id TEXT NOT NULL,
                source TEXT NOT NULL, page INTEGER NOT NULL, content TEXT NOT NULL,
                metadata JSONB NOT NULL DEFAULT '{{}}'::jsonb,
                embedding vector({self.dimensions}) NOT NULL,
                PRIMARY KEY (strategy, chunk_id))""")
            conn.execute("CREATE INDEX IF NOT EXISTS day6_chunks_metadata_idx ON day6_chunks USING gin (metadata)")

    def upsert(self, strategy: str, chunks: list[Chunk], vectors: list[list[float]]) -> None:
        """Replace a strategy atomically to remove chunks made obsolete by re-ingest."""
        if len(chunks) != len(vectors):
            raise ValueError("chunks and vectors must have equal lengths")
        for vector in vectors:
            if len(vector) != self.dimensions:
                raise ValueError(f"Expected {self.dimensions}-dimension vector")
        with psycopg.connect(self.database_url) as conn:
            conn.execute("DELETE FROM day6_chunks WHERE strategy=%s", (strategy,))
            with conn.cursor() as cursor:
                cursor.executemany("""INSERT INTO day6_chunks
                    (strategy,chunk_id,document_id,source,page,content,metadata,embedding)
                    VALUES (%s,%s,%s,%s,%s,%s,%s,%s::vector)""",
                    [(strategy, c.chunk_id, c.document_id, c.source, c.page, c.text,
                      Jsonb(c.metadata), "[" + ",".join(map(str, v)) + "]")
                     for c, v in zip(chunks, vectors)])

    def search(self, strategy: str, query_vector: list[float], top_k: int = 3,
               filters: dict[str, Any] | None = None) -> list[dict[str, Any]]:
        """Apply exact JSONB metadata filters before cosine ranking."""
        if len(query_vector) != self.dimensions:
            raise ValueError(f"Expected {self.dimensions}-dimension query vector")
        if top_k < 1:
            return []
        vector = "[" + ",".join(map(str, query_vector)) + "]"
        with psycopg.connect(self.database_url) as conn:
            rows = conn.execute("""SELECT chunk_id,document_id,source,page,content,metadata,
                    1 - (embedding <=> %s::vector) AS score
                FROM day6_chunks WHERE strategy=%s AND metadata @> %s
                ORDER BY embedding <=> %s::vector LIMIT %s""",
                (vector, strategy, Jsonb(filters or {}), vector, top_k)).fetchall()
        return [{"chunk_id": r[0], "document_id": r[1], "source": r[2],
                 "page": r[3], "text": r[4], "metadata": r[5], "score": float(r[6])}
                for r in rows]
