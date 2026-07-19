"""
Autonomous analysis.

Runs automatically after upload/cleaning to surface relationships and
trends without the user having to ask a specific question first. This is
what item 5 of the spec ("autonomous AI analysis") maps to — everything
here is computed with real statistics; only the final plain-English
summary goes through the LLM, and it's given the computed numbers rather
than asked to invent them.
"""

import pandas as pd
import numpy as np

from app.ai_analyst.llm_client import get_llm_client


def compute_correlations(df: pd.DataFrame, top_n: int = 8) -> dict:
    numeric_df = df.select_dtypes(include=[np.number])
    if numeric_df.shape[1] < 2:
        return {"matrix": {}, "top_pairs": []}

    corr = numeric_df.corr(numeric_only=True).round(3)
    matrix = corr.to_dict()

    pairs = []
    cols = corr.columns.tolist()
    for i, col_a in enumerate(cols):
        for col_b in cols[i + 1:]:
            value = corr.loc[col_a, col_b]
            if pd.notna(value):
                pairs.append({"column_a": col_a, "column_b": col_b, "correlation": float(value)})

    pairs.sort(key=lambda p: abs(p["correlation"]), reverse=True)
    return {"matrix": matrix, "top_pairs": pairs[:top_n]}


def detect_trends(df: pd.DataFrame) -> list[dict]:
    """For each numeric column with a usable date column, fit a simple
    linear trend and report the direction/strength — same method as the
    forecast branch, reused here for a dataset-wide overview."""
    date_col = None
    for col in df.columns:
        if pd.api.types.is_datetime64_any_dtype(df[col]):
            date_col = col
            break
        if any(k in col.lower() for k in ("date", "month", "period", "time")):
            try:
                pd.to_datetime(df[col].dropna().head(20))
                date_col = col
                break
            except Exception:
                continue

    if not date_col:
        return []

    trends = []
    working_dates = pd.to_datetime(df[date_col], errors="coerce")

    for col in df.select_dtypes(include=[np.number]).columns:
        temp = pd.DataFrame({"_date": working_dates, "_val": df[col]}).dropna()
        if len(temp) < 6:
            continue
        temp["_period"] = temp["_date"].dt.to_period("M")
        monthly = temp.groupby("_period")["_val"].sum().sort_index()
        if len(monthly) < 3:
            continue

        x = np.arange(len(monthly))
        y = monthly.values
        slope, intercept = np.polyfit(x, y, 1)
        y_pred = slope * x + intercept
        ss_res = np.sum((y - y_pred) ** 2)
        ss_tot = np.sum((y - y.mean()) ** 2)
        r_squared = float(1 - ss_res / ss_tot) if ss_tot != 0 else 0.0

        trends.append({
            "column": col,
            "direction": "increasing" if slope > 0 else "decreasing",
            "slope_per_period": round(float(slope), 3),
            "r_squared": round(r_squared, 3),
            "periods_available": len(monthly),
        })

    trends.sort(key=lambda t: t["r_squared"], reverse=True)
    return trends


def detect_important_variables(df: pd.DataFrame, correlations: dict) -> list[str]:
    """Heuristic: a variable is 'important' if it's strongly correlated with
    at least one other variable, or if it's a likely business metric by name."""
    important = set()
    for pair in correlations.get("top_pairs", []):
        if abs(pair["correlation"]) > 0.5:
            important.add(pair["column_a"])
            important.add(pair["column_b"])

    priority_keywords = ["revenue", "sales", "profit", "churn", "price", "cost"]
    for col in df.columns:
        if any(kw in col.lower() for kw in priority_keywords):
            important.add(col)

    return list(important)


def generate_autonomous_summary(df: pd.DataFrame, domain: str) -> dict:
    correlations = compute_correlations(df)
    trends = detect_trends(df)
    important_variables = detect_important_variables(df, correlations)

    llm = get_llm_client()
    findings_context = (
        f"Domain: {domain}\n"
        f"Top correlations: {correlations['top_pairs'][:5]}\n"
        f"Trends detected: {trends[:5]}\n"
        f"Variables flagged as important: {important_variables}\n"
    )

    summary = llm.generate_dataset_summary(findings_context)

    return {
        "correlations": correlations,
        "trends": trends,
        "important_variables": important_variables,
        "summary": summary,
    }
