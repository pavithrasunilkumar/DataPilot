"""
AI Analyst pipeline — orchestrates one question end to end:

  question
    -> schema description
    -> SQL generation (LLM)
    -> safe SQL execution (DuckDB)
    -> real significance test (scipy, NOT the LLM)
    -> explanation (LLM, grounded in the computed stats)
    -> Skeptic Agent critique (concrete checks, not just LLM opinion)
    -> Insight Diffing against past questions on this dataset

The LLM only ever translates (question -> SQL, result -> explanation).
All computation is done by DuckDB/pandas/scipy.
"""

from app.ai_analyst.llm_client import get_llm_client
from app.ai_analyst.schema_utils import describe_schema, guess_date_column, guess_numeric_target_column
from app.ai_analyst.query_executor import run_query, load_dataframe, UnsafeQueryError
from app.ai_analyst.stats_engine import compare_last_two_periods
from app.ai_analyst.skeptic import critique_insight
from app.ai_analyst.diffing import find_most_similar_past_insight
from app.rag.store import retrieve_context


def answer_question(dataset_id: str, question: str, file_path: str, past_insights: list) -> dict:
    df = load_dataframe(file_path)
    schema_description = describe_schema(df)

    date_col = guess_date_column(df)
    value_col = guess_numeric_target_column(df, question)

    llm = get_llm_client()

    # --- RAG: pull schema notes, business glossary, and past findings ---
    rag_context = retrieve_context(dataset_id, question)

    # --- SQL generation + execution ---
    sql_template = llm.generate_sql(question, schema_description, context=rag_context)
    if date_col and value_col and "{date_col}" in sql_template:
        sql = sql_template.replace("{date_col}", date_col).replace("{value_col}", value_col)
    else:
        sql = sql_template

    try:
        result = run_query(file_path, sql) if "{" not in sql else []
    except (UnsafeQueryError, Exception):
        result = []

    # --- Real statistical test (independent of the LLM) ---
    stat_test = None
    if date_col and value_col:
        stat_test = compare_last_two_periods(df, date_col, value_col)

    # --- Explanation (grounded in the computed stat_test, not invented) ---
    explanation = llm.generate_explanation(question, sql, result, stat_test, context=rag_context)

    # --- Skeptic Agent ---
    critique = critique_insight(stat_test, total_row_count=len(df))

    # --- Insight Diffing ---
    diff_summary = None
    compared_insight_id = None
    match = find_most_similar_past_insight(question, past_insights)
    if match:
        past_insight, similarity = match
        diff_summary = llm.generate_diff_summary(question, past_insight.explanation or "", explanation)
        compared_insight_id = past_insight.id

    confidence_score = _estimate_confidence(stat_test, critique)

    return {
        "sql": sql,
        "result": result,
        "stat_test": stat_test,
        "explanation": explanation,
        "critique": critique,
        "diff_summary": diff_summary,
        "compared_insight_id": compared_insight_id,
        "confidence_score": confidence_score,
        "date_column_used": date_col,
        "value_column_used": value_col,
        "rag_context_used": rag_context,
    }


def _estimate_confidence(stat_test: dict | None, critique: dict) -> float:
    """
    Confidence is derived from concrete signals, not asserted by the LLM:
    starts high, is reduced by each Skeptic Agent flag's severity.
    """
    if stat_test is None:
        return 35.0

    score = 90.0
    severity_penalty = {"high": 25, "medium": 12, "low": 5, "info": 0}
    for flag in critique.get("flags", []):
        score -= severity_penalty.get(flag["severity"], 0)

    return max(10.0, round(score, 1))
