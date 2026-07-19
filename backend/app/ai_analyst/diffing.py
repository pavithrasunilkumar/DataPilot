"""
Insight Diffing.

Compares a newly generated insight against past insights asked on the
same dataset. If a similar question was asked before, this surfaces
whether the conclusion has changed — like a git diff, but for business
conclusions rather than code.

Uses TF-IDF + cosine similarity for "is this a similar question" matching.
This is intentionally lightweight (no heavy embedding model dependency) —
it's a drop-in upgrade path to swap in sentence-transformers + Chroma
later without changing the interface this module exposes.
"""

from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

SIMILARITY_THRESHOLD = 0.35


def find_most_similar_past_insight(new_question: str, past_insights: list) -> tuple | None:
    """
    past_insights: list of Insight ORM objects (must have .question, .explanation, .id)
    Returns (insight, similarity_score) for the closest match above threshold, or None.
    """
    if not past_insights:
        return None

    corpus = [new_question] + [i.question for i in past_insights]
    vectorizer = TfidfVectorizer(stop_words="english")

    try:
        tfidf_matrix = vectorizer.fit_transform(corpus)
    except ValueError:
        # happens if the corpus is too small / all-stopwords — nothing to compare against
        return None

    similarities = cosine_similarity(tfidf_matrix[0:1], tfidf_matrix[1:])[0]
    best_idx = similarities.argmax()
    best_score = float(similarities[best_idx])

    if best_score < SIMILARITY_THRESHOLD:
        return None

    return past_insights[best_idx], round(best_score, 3)
