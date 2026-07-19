"""
RAG (Retrieval-Augmented Generation) layer.

Before the LLM writes a SQL query or an explanation, this module retrieves
the context it actually needs to be correct for THIS dataset:
  - schema documentation (column names, types, sample values)
  - the business glossary for the detected domain (so "churn" means the
    right thing for retail vs finance vs healthcare)
  - past insights on this same dataset (so answers stay consistent over time)

Retrieval uses TF-IDF + cosine similarity. This is intentionally lightweight
— no embedding model or vector database dependency — so it runs anywhere
with zero setup. It's a drop-in upgrade path to swap in sentence-transformers
+ Chroma later without changing the interface this module exposes
(the same approach used in diffing.py).
"""

from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

from app.ai_analyst.schema_utils import describe_schema, detect_domain, get_glossary

TOP_K_PAST_INSIGHTS = 3


def _retrieve_top_k(query: str, documents: list[str], k: int) -> list[int]:
    """Returns indices of the top-k most relevant documents to the query."""
    if not documents:
        return []
    corpus = [query] + documents
    vectorizer = TfidfVectorizer(stop_words="english")
    try:
        matrix = vectorizer.fit_transform(corpus)
    except ValueError:
        return []
    similarities = cosine_similarity(matrix[0:1], matrix[1:])[0]
    ranked = similarities.argsort()[::-1][:k]
    return [i for i in ranked if similarities[i] > 0]


def build_context(question: str, df, past_insights: list) -> dict:
    """
    Returns a dict with the retrieved context pieces, plus a combined
    `context_text` string ready to inject into an LLM prompt.
    """
    domain = detect_domain(df)
    schema_text = describe_schema(df)

    glossary = get_glossary(domain)
    relevant_glossary_terms = {
        term: definition for term, definition in glossary.items() if term.split()[0] in question.lower()
    }
    # If nothing matched directly, still surface the domain glossary — it's small
    # enough that showing all of it costs little and helps the LLM anyway.
    if not relevant_glossary_terms:
        relevant_glossary_terms = glossary

    past_insight_texts = [f"Q: {i.question}\nA: {i.explanation or ''}" for i in past_insights]
    top_indices = _retrieve_top_k(question, past_insight_texts, TOP_K_PAST_INSIGHTS)
    relevant_past_insights = [past_insight_texts[i] for i in top_indices]

    glossary_text = "\n".join(f"- {term}: {definition}" for term, definition in relevant_glossary_terms.items())
    past_insights_text = "\n---\n".join(relevant_past_insights)

    context_text = (
        f"Detected business domain: {domain}\n\n"
        f"Schema:\n{schema_text}\n\n"
        f"Business glossary ({domain}):\n{glossary_text or '(none)'}\n\n"
        f"Relevant past findings on this dataset:\n{past_insights_text or '(none yet)'}"
    )

    return {
        "domain": domain,
        "schema_text": schema_text,
        "glossary": relevant_glossary_terms,
        "relevant_past_insights": relevant_past_insights,
        "context_text": context_text,
    }
