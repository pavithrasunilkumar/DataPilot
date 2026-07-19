"""
LLM client abstraction.

Two modes:
- "groq"     — calls the real Groq API (OpenAI-compatible). Requires GROQ_API_KEY.
- "fallback" — deterministic, rule-based responses. No network, no key needed.
               Used automatically when no API key is configured, so the whole
               pipeline stays testable and demoable without any external dependency.

Both modes implement the same interface, so the rest of the pipeline
(pipeline.py, skeptic.py, diffing.py) never needs to know which one is active.
"""

from app.core.config import settings


class LLMClient:
    def generate_sql(self, question: str, schema_description: str, context: str = "") -> str:
        raise NotImplementedError

    def generate_explanation(self, question: str, sql: str, result: list[dict], stat_test: dict | None, context: str = "") -> str:
        raise NotImplementedError

    def generate_diff_summary(self, question: str, old_explanation: str, new_explanation: str) -> str:
        raise NotImplementedError

    def generate_dataset_summary(self, context: str) -> str:
        raise NotImplementedError


class FallbackLLMClient(LLMClient):
    """
    Deterministic, template-based responses. This is NOT meant to be
    intelligent — it exists so the pipeline is fully runnable and testable
    without a paid/rate-limited API key. Swap in GroqLLMClient for real
    natural-language understanding.
    """

    def generate_sql(self, question: str, schema_description: str, context: str = "") -> str:
        # Extremely simple heuristic: look for a numeric column name mentioned
        # in the question, plus a date-like column, and build a monthly trend query.
        return (
            "-- [demo mode: no LLM configured] heuristic query, not truly NL-driven\n"
            "SELECT date_trunc('month', CAST({date_col} AS DATE)) AS period, SUM({value_col}) AS total\n"
            "FROM dataset\n"
            "GROUP BY 1\n"
            "ORDER BY 1;"
        )

    def generate_explanation(self, question: str, sql: str, result: list[dict], stat_test: dict | None, context: str = "") -> str:
        if not result:
            return "No rows were returned for this question — the underlying data may not cover it."

        trend_note = ""
        if stat_test:
            sig = "a statistically significant" if stat_test.get("p_value", 1) < 0.05 else "not a statistically significant"
            trend_note = (
                f" The difference between the two most recent periods is {sig} change "
                f"(t-test, p = {stat_test.get('p_value'):.3f})."
            )

        return (
            f"Based on the query result, here is what the data shows for \"{question}\": "
            f"the most recent period's value differs from the prior period."
            f"{trend_note} "
            f"[Demo mode: connect a GROQ_API_KEY for a real natural-language explanation.]"
        )

    def generate_diff_summary(self, question: str, old_explanation: str, new_explanation: str) -> str:
        if old_explanation.strip() == new_explanation.strip():
            return "The conclusion is unchanged since the last time a similar question was asked."
        return (
            "This conclusion differs from the last similar question asked on this dataset. "
            "Previously: \"" + old_explanation[:160] + ("..." if len(old_explanation) > 160 else "") + "\" "
            "Now: \"" + new_explanation[:160] + ("..." if len(new_explanation) > 160 else "") + "\" "
            "Review whether the underlying driver has genuinely changed or whether this reflects noise."
        )

    def generate_dataset_summary(self, context: str) -> str:
        # Built directly from the structured findings passed in `context`
        # (correlations/trends/important variables) rather than a generic
        # "no rows returned" template, which doesn't apply to a whole-dataset
        # summary that never runs a single SQL query in the first place.
        return (
            "Dataset summary (demo mode — connect a GROQ_API_KEY for a natural-language write-up): "
            f"{context.strip()[:500]}"
        )


class GroqLLMClient(LLMClient):
    """Real LLM calls via Groq's OpenAI-compatible API. Requires `groq` package + API key."""

    def __init__(self):
        from groq import Groq  # imported lazily so the package is optional in fallback mode
        self.client = Groq(api_key=settings.groq_api_key)
        self.model = "llama-3.3-70b-versatile"

    def _chat(self, prompt: str) -> str:
        response = self.client.chat.completions.create(
            model=self.model,
            messages=[{"role": "user", "content": prompt}],
            temperature=0.2,
        )
        return response.choices[0].message.content.strip()

    def generate_sql(self, question: str, schema_description: str, context: str = "") -> str:
        prompt = (
            f"Relevant context (business glossary, schema notes, past findings):\n{context}\n\n"
            f"Table schema:\n{schema_description}\n\n"
            f"Question: {question}\n\n"
            "Write ONLY a single DuckDB SQL query against a table named `dataset` "
            "that helps answer this question. No explanation, no markdown fences."
        )
        return self._chat(prompt)

    def generate_explanation(self, question: str, sql: str, result: list[dict], stat_test: dict | None, context: str = "") -> str:
        prompt = (
            f"Relevant context:\n{context}\n\n"
            f"Question: {question}\nSQL used: {sql}\nResult: {result}\n"
            f"Statistical test result: {stat_test}\n\n"
            "Write a concise, plain-English business explanation and a recommendation. "
            "Use the business glossary/context above to interpret terms the way this specific "
            "business defines them. State clearly whether the pattern is statistically significant, "
            "don't invent numbers that aren't in the result or test output."
        )
        return self._chat(prompt)

    def generate_diff_summary(self, question: str, old_explanation: str, new_explanation: str) -> str:
        prompt = (
            f"A user previously asked a similar question and got this conclusion:\n{old_explanation}\n\n"
            f"They just asked again and got this new conclusion:\n{new_explanation}\n\n"
            "In 2-3 sentences, state whether the conclusion has changed, and if so, what that "
            "implies. Be direct about contradictions."
        )
        return self._chat(prompt)

    def generate_dataset_summary(self, context: str) -> str:
        prompt = (
            f"Here are computed findings about a dataset:\n{context}\n\n"
            "Write a concise (3-5 sentence) plain-English summary of the key relationships, "
            "trends, and important variables for a business reader. Only describe what's in the "
            "findings above — don't invent numbers that aren't there."
        )
        return self._chat(prompt)


def get_llm_client() -> LLMClient:
    if settings.llm_provider == "groq" and settings.groq_api_key:
        try:
            return GroqLLMClient()
        except Exception:
            # Falls back gracefully rather than crashing the whole pipeline
            # if the groq package isn't installed or the key is invalid.
            return FallbackLLMClient()
    return FallbackLLMClient()
