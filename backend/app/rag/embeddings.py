"""
Embedding function used by the RAG vector store.

Two backends, chosen by settings.embedding_backend:

- "hashing" (default) — scikit-learn's HashingVectorizer. Fixed-dimension,
  fully deterministic, zero downloads, zero external dependencies. This is
  what makes the whole RAG layer runnable offline / in CI / in this repo's
  automated tests with no setup step. It captures lexical similarity well
  (shared words, phrasing) but not true semantic similarity (synonyms).

- "sentence-transformers" — swaps in a real embedding model
  (all-MiniLM-L6-v2) for genuine semantic matching (e.g. "decline" and
  "decrease" will match). Requires `pip install sentence-transformers`
  and a one-time model download on first use. This is the recommended
  backend for a real deployment; "hashing" is the safe default so the
  project works immediately with no extra setup.

Both implement the same Chroma EmbeddingFunction protocol, so nothing
else in the RAG/pipeline code needs to change when you switch backends.
"""

from sklearn.feature_extraction.text import HashingVectorizer

from app.core.config import settings


class HashingEmbeddingFunction:
    """Zero-dependency, deterministic embedding — the default backend."""

    def __init__(self, n_features: int = 384):
        self.vectorizer = HashingVectorizer(
            n_features=n_features, alternate_sign=False, norm="l2"
        )

    def __call__(self, input):
        return self.vectorizer.transform(input).toarray().tolist()

    def embed_query(self, input):
        return self.__call__(input)

    def name(self):
        return "hashing-vectorizer-384"

    def is_legacy(self):
        return False


class SentenceTransformerEmbeddingFunction:
    """Real semantic embeddings. Requires `sentence-transformers` installed."""

    def __init__(self, model_name: str = "all-MiniLM-L6-v2"):
        from sentence_transformers import SentenceTransformer  # optional dependency
        self.model = SentenceTransformer(model_name)

    def __call__(self, input):
        return self.model.encode(input, convert_to_numpy=True).tolist()

    def embed_query(self, input):
        return self.__call__(input)

    def name(self):
        return "sentence-transformers-all-MiniLM-L6-v2"


def get_embedding_function():
    if settings.embedding_backend == "sentence-transformers":
        try:
            return SentenceTransformerEmbeddingFunction()
        except Exception:
            # Falls back rather than crashing the app if the optional
            # dependency isn't installed or the model can't be downloaded.
            return HashingEmbeddingFunction()
    return HashingEmbeddingFunction()
