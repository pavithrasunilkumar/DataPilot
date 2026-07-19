"""
Agentic orchestration via LangGraph.

Replaces a fixed linear pipeline with a graph that can actually make
decisions:

  classify_intent
      |-- "forecast"  --> forecast_node ------------------------> diff --> END
      |-- "diagnostic" --> retrieve_context -> generate_sql -> execute_sql
                                                                     |
                                                    (empty result, retry budget left)
                                                                     |
                                                            <-- retry: generate_sql
                                                                     |
                                                              run_stats -> explain
                                                                              |
                                                                           skeptic
                                                                              |
                                                                            diff --> END

This is what makes the pipeline "agentic" rather than a straight script:
it decides which path a question needs, and recovers from a failed/empty
query by retrying once with a reformulated attempt instead of just
returning nothing.
"""

from typing import TypedDict, Optional
from langgraph.graph import StateGraph, END

from app.ai_analyst.llm_client import get_llm_client
from app.ai_analyst.schema_utils import describe_schema, guess_date_column, guess_numeric_target_column
from app.ai_analyst.query_executor import run_query, load_dataframe, UnsafeQueryError
from app.ai_analyst.stats_engine import compare_last_two_periods
from app.ai_analyst.skeptic import critique_insight
from app.ai_analyst.diffing import find_most_similar_past_insight
from app.ai_analyst.forecast import simple_linear_forecast
from app.rag.store import retrieve_context

FORECAST_KEYWORDS = ("forecast", "predict", "next month", "next quarter", "will ", "expected to", "projection")


class AnalystState(TypedDict, total=False):
    dataset_id: str
    question: str
    file_path: str
    past_insights: list

    intent: str
    schema_description: str
    date_col: Optional[str]
    value_col: Optional[str]
    rag_context: str

    sql: str
    result: list
    retry_count: int

    stat_test: Optional[dict]
    forecast: Optional[dict]
    explanation: str
    critique: dict
    diff_summary: Optional[str]
    compared_insight_id: Optional[str]
    confidence_score: float


def _classify_intent(state: AnalystState) -> AnalystState:
    q = state["question"].lower()
    intent = "forecast" if any(kw in q for kw in FORECAST_KEYWORDS) else "diagnostic"

    df = load_dataframe(state["file_path"])
    state["schema_description"] = describe_schema(df)
    state["date_col"] = guess_date_column(df)
    state["value_col"] = guess_numeric_target_column(df, state["question"])
    state["intent"] = intent
    state["retry_count"] = 0
    return state


def _retrieve_context(state: AnalystState) -> AnalystState:
    state["rag_context"] = retrieve_context(state["dataset_id"], state["question"])
    return state


def _generate_sql(state: AnalystState) -> AnalystState:
    llm = get_llm_client()
    template = llm.generate_sql(state["question"], state["schema_description"], context=state["rag_context"])

    date_col, value_col = state.get("date_col"), state.get("value_col")
    if date_col and value_col and "{date_col}" in template:
        sql = template.replace("{date_col}", date_col).replace("{value_col}", value_col)
    else:
        sql = template
    state["sql"] = sql
    return state


def _execute_sql(state: AnalystState) -> AnalystState:
    sql = state["sql"]
    try:
        state["result"] = run_query(state["file_path"], sql) if "{" not in sql else []
    except (UnsafeQueryError, Exception):
        state["result"] = []
    return state


def _should_retry(state: AnalystState) -> str:
    if not state["result"] and state["retry_count"] < 1:
        return "retry"
    return "continue"


def _increment_retry(state: AnalystState) -> AnalystState:
    state["retry_count"] = state.get("retry_count", 0) + 1
    return state


def _run_stats(state: AnalystState) -> AnalystState:
    df = load_dataframe(state["file_path"])
    date_col, value_col = state.get("date_col"), state.get("value_col")
    state["stat_test"] = compare_last_two_periods(df, date_col, value_col) if date_col and value_col else None
    return state


def _explain(state: AnalystState) -> AnalystState:
    llm = get_llm_client()
    state["explanation"] = llm.generate_explanation(
        state["question"], state["sql"], state["result"], state.get("stat_test"), context=state["rag_context"]
    )
    return state


def _forecast_node(state: AnalystState) -> AnalystState:
    df = load_dataframe(state["file_path"])
    date_col, value_col = state.get("date_col"), state.get("value_col")
    forecast = simple_linear_forecast(df, date_col, value_col) if date_col and value_col else None
    state["forecast"] = forecast
    state["rag_context"] = ""  # forecast branch doesn't currently pull RAG context

    if forecast is None:
        state["explanation"] = "Not enough historical periods were found to build a reliable forecast."
        state["stat_test"] = None
    else:
        direction = "increase" if forecast["trend_slope_per_period"] > 0 else "decrease"
        state["explanation"] = (
            f"Based on a linear trend across {forecast['periods_used']} periods, {value_col} is "
            f"projected to {direction} to approximately {forecast['predicted_value']} in "
            f"{forecast['next_period']} (trend fit R\u00b2 = {forecast['r_squared']}). "
            "This is a simple trend extrapolation, not a seasonally-adjusted model — treat it as "
            "a directional signal rather than a precise prediction."
        )
        state["stat_test"] = None  # significance testing doesn't apply to a trend extrapolation
    state["sql"] = "-- forecast branch: no SQL executed, trend computed directly from raw data"
    state["result"] = []
    return state


def _skeptic(state: AnalystState) -> AnalystState:
    df = load_dataframe(state["file_path"])

    if state["intent"] == "forecast":
        # The generic critique_insight() assumes a None stat_test means "not
        # enough data for ANY analysis" — which is wrong here, since the
        # forecast branch deliberately doesn't run a significance test at all.
        # Build a forecast-specific critique instead.
        forecast = state.get("forecast")
        flags = [{
            "type": "correlation_not_causation",
            "severity": "info",
            "message": (
                "A trend line describes the historical pattern; it does not prove the "
                "underlying cause will continue unchanged."
            ),
        }]
        trust_level = "medium"

        if forecast is None:
            flags.append({
                "type": "insufficient_data",
                "severity": "high",
                "message": "Not enough historical periods were available to fit a trend line.",
            })
            trust_level = "low"
        elif forecast["r_squared"] < 0.3:
            flags.append({
                "type": "poor_trend_fit",
                "severity": "high",
                "message": (
                    f"The linear trend only explains {round(forecast['r_squared'] * 100)}% of the "
                    "variation in the data (R\u00b2). The forecast should be treated as low-confidence."
                ),
            })
            trust_level = "low"
        elif forecast["periods_used"] < 6:
            flags.append({
                "type": "short_history",
                "severity": "medium",
                "message": (
                    f"Only {forecast['periods_used']} periods of history back this forecast — "
                    "more history would make the projection more reliable."
                ),
            })
            trust_level = "medium"

        state["critique"] = {"flags": flags, "trust_level": trust_level}
        return state

    state["critique"] = critique_insight(state.get("stat_test"), total_row_count=len(df))
    return state


def _diff(state: AnalystState) -> AnalystState:
    llm = get_llm_client()
    match = find_most_similar_past_insight(state["question"], state.get("past_insights", []))
    if match:
        past_insight, _similarity = match
        state["diff_summary"] = llm.generate_diff_summary(
            state["question"], past_insight.explanation or "", state["explanation"]
        )
        state["compared_insight_id"] = past_insight.id
    else:
        state["diff_summary"] = None
        state["compared_insight_id"] = None

    state["confidence_score"] = _estimate_confidence(state)
    return state


def _estimate_confidence(state: AnalystState) -> float:
    if state["intent"] == "forecast":
        forecast = state.get("forecast")
        if forecast is None:
            return 20.0
        base = 40.0 + forecast["r_squared"] * 50.0  # R^2 of 1.0 -> ~90, R^2 of 0 -> ~40
        return round(base, 1)

    if state.get("stat_test") is None:
        return 35.0

    score = 90.0
    severity_penalty = {"high": 25, "medium": 12, "low": 5, "info": 0}
    for flag in state["critique"].get("flags", []):
        score -= severity_penalty.get(flag["severity"], 0)
    return max(10.0, round(score, 1))


def _route_by_intent(state: AnalystState) -> str:
    return "forecast" if state["intent"] == "forecast" else "diagnostic"


def build_graph():
    graph = StateGraph(AnalystState)

    graph.add_node("classify_intent", _classify_intent)
    graph.add_node("retrieve_context", _retrieve_context)
    graph.add_node("generate_sql", _generate_sql)
    graph.add_node("execute_sql", _execute_sql)
    graph.add_node("increment_retry", _increment_retry)
    graph.add_node("run_stats", _run_stats)
    graph.add_node("explain", _explain)
    graph.add_node("forecast_node", _forecast_node)
    graph.add_node("skeptic", _skeptic)
    graph.add_node("diff", _diff)

    graph.set_entry_point("classify_intent")

    graph.add_conditional_edges(
        "classify_intent", _route_by_intent,
        {"forecast": "forecast_node", "diagnostic": "retrieve_context"},
    )

    graph.add_edge("retrieve_context", "generate_sql")
    graph.add_edge("generate_sql", "execute_sql")
    graph.add_conditional_edges(
        "execute_sql", _should_retry,
        {"retry": "increment_retry", "continue": "run_stats"},
    )
    graph.add_edge("increment_retry", "generate_sql")
    graph.add_edge("run_stats", "explain")
    graph.add_edge("explain", "skeptic")
    graph.add_edge("forecast_node", "skeptic")
    graph.add_edge("skeptic", "diff")
    graph.add_edge("diff", END)

    return graph.compile()


_compiled_graph = None


def get_graph():
    global _compiled_graph
    if _compiled_graph is None:
        _compiled_graph = build_graph()
    return _compiled_graph


def run_agentic_analysis(dataset_id: str, question: str, file_path: str, past_insights: list) -> dict:
    graph = get_graph()
    initial_state: AnalystState = {
        "dataset_id": dataset_id,
        "question": question,
        "file_path": file_path,
        "past_insights": past_insights,
    }
    final_state = graph.invoke(initial_state)
    return dict(final_state)
