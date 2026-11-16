"""Choose a real embedding provider (API or local) and implement this contract."""
from typing import Protocol


class Embedder(Protocol):
    model_name: str
    dimensions: int

    def embed_documents(self, texts: list[str]) -> list[list[float]]:
        """Return one vector per input text, in the same order."""
        ...

    def embed_query(self, question: str) -> list[float]:
        """Return a query vector compatible with the stored document vectors."""
        ...


class MyEmbedder:
    """Sentence Transformers adapter; never silently substitutes another model."""

    def __init__(self, model_name: str, local_files_only: bool = False) -> None:
        from sentence_transformers import SentenceTransformer
        self.model_name = model_name
        self._model = SentenceTransformer(model_name, local_files_only=local_files_only)
        get_dimension = getattr(self._model, "get_embedding_dimension", None)
        self.dimensions = (get_dimension() if get_dimension
                           else self._model.get_sentence_embedding_dimension())
        if not self.dimensions:
            raise RuntimeError(f"Could not determine dimensions for {model_name}")

    def embed_documents(self, texts: list[str]) -> list[list[float]]:
        if not texts:
            return []
        return self._model.encode(texts, normalize_embeddings=True,
                                  convert_to_numpy=True).tolist()

    def embed_query(self, question: str) -> list[float]:
        return self._model.encode([question], normalize_embeddings=True,
                                  convert_to_numpy=True)[0].tolist()

    def count_tokens(self, texts: list[str]) -> int:
        """Count tokenizer inputs using the model's configured truncation limit."""
        total = 0
        for start in range(0, len(texts), 64):
            batch = self._model.tokenizer(texts[start:start + 64], padding=False,
                                          truncation=True, max_length=self._model.max_seq_length)
            total += sum(len(ids) for ids in batch["input_ids"])
        return total
