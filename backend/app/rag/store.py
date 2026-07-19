"""
RAG vector store. Wraps Chroma with three per-dataset collections:

- schema_docs      — column name -> plain-English meaning
- business_glossary — domain-specific term definitions
- past_insights     — every prior AI Analyst question + explanation on this dataset

Each dataset gets its own isolated set of collections (namespaced by
dataset_id) so one business's data/vocabulary never leaks into another's
context.
"""

import chromadb
from chromadb.config import Settings as ChromaSettings

from app.core.config import settings
from app.rag.embeddings import get_embedding_function

_client = None


def get_chroma_client():
    global _client
    if _client is None:
        _client = chromadb.PersistentClient(
            path=settings.chroma_persist_dir,
            settings=ChromaSettings(anonymized_telemetry=False),
        )
    return _client


def _collection_name(dataset_id: str, kind: str) -> str:
    # Chroma collection names must be simple strings — keep them short and safe.
    return f"{kind}_{dataset_id}"[:63]


def get_collection(dataset_id: str, kind: str):
    client = get_chroma_client()
    return client.get_or_create_collection(
        name=_collection_name(dataset_id, kind),
        embedding_function=get_embedding_function(),
    )


def index_schema_docs(dataset_id: str, column_descriptions: dict[str, str]):
    """column_descriptions: {column_name: plain-English description}"""
    if not column_descriptions:
        return
    collection = get_collection(dataset_id, "schema")
    collection.upsert(
        documents=list(column_descriptions.values()),
        ids=[f"col_{name}" for name in column_descriptions.keys()],
        metadatas=[{"column": name} for name in column_descriptions.keys()],
    )


def index_glossary_terms(dataset_id: str, glossary: dict[str, str]):
    """glossary: {term: business-specific definition}"""
    if not glossary:
        return
    collection = get_collection(dataset_id, "glossary")
    collection.upsert(
        documents=list(glossary.values()),
        ids=[f"term_{term}" for term in glossary.keys()],
        metadatas=[{"term": term} for term in glossary.keys()],
    )


def index_insight(dataset_id: str, insight_id: str, question: str, explanation: str):
    collection = get_collection(dataset_id, "insights")
    collection.upsert(
        documents=[f"Q: {question}\nA: {explanation}"],
        ids=[insight_id],
        metadatas=[{"question": question}],
    )


def retrieve_context(dataset_id: str, question: str, k: int = 3) -> str:
    """
    Pulls the top-k most relevant chunks from all three collections and
    returns them as a single formatted context block, ready to inject into
    the LLM prompt.
    """
    sections = []

    for kind, label in (("schema", "Schema notes"), ("glossary", "Business glossary"), ("insights", "Past findings")):
        try:
            collection = get_collection(dataset_id, kind)
            if collection.count() == 0:
                continue
            results = collection.query(query_texts=[question], n_results=min(k, collection.count()))
            docs = results.get("documents", [[]])[0]
            if docs:
                sections.append(f"{label}:\n" + "\n".join(f"- {d}" for d in docs))
        except Exception:
            continue  # a missing/empty collection should never break the pipeline

    return "\n\n".join(sections) if sections else "(no prior context available for this dataset yet)"
