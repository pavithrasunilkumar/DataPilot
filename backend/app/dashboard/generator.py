"""
Dashboard generator.

Produces a JSON spec describing every chart the frontend should render —
KPI cards, correlation heatmap, histograms, missing-value chart, top
categorical bar chart, time series, and feature importance (if a model has
been trained). No image rendering happens server-side; the frontend uses
this structured data with Recharts, which keeps the payload small and the
charts properly interactive/responsive rather than static images.
"""

import pandas as pd
import numpy as np

from app.data.auto_analysis import compute_correlations, detect_trends


def _numeric_histogram(series: pd.Series, bins: int = 10) -> list[dict]:
    clean = series.dropna()
    if clean.empty:
        return []
    counts, edges = np.histogram(clean, bins=bins)
    return [
        {"bucket": f"{edges[i]:.1f}–{edges[i+1]:.1f}", "count": int(counts[i])}
        for i in range(len(counts))
    ]


def _top_categories(series: pd.Series, top_n: int = 8) -> list[dict]:
    counts = series.value_counts(dropna=True).head(top_n)
    return [{"category": str(k), "count": int(v)} for k, v in counts.items()]


def _missing_value_chart(df: pd.DataFrame) -> list[dict]:
    return [
        {"column": col, "missing_pct": round(float(df[col].isna().sum() / len(df) * 100), 2)}
        for col in df.columns
    ] if len(df) else []


def _kpi_cards(df: pd.DataFrame, quality_score: float | None, domain: str | None) -> list[dict]:
    cards = [
        {"label": "Rows", "value": len(df)},
        {"label": "Columns", "value": len(df.columns)},
    ]
    if quality_score is not None:
        cards.append({"label": "Quality Score", "value": quality_score, "unit": "/ 100"})

    numeric_cols = df.select_dtypes(include=[np.number]).columns
    priority_keywords = ["revenue", "sales", "profit", "amount", "price"]
    key_metric_col = None
    for kw in priority_keywords:
        for col in numeric_cols:
            if kw in col.lower():
                key_metric_col = col
                break
        if key_metric_col:
            break
    if key_metric_col is None and len(numeric_cols) > 0:
        key_metric_col = numeric_cols[0]

    if key_metric_col is not None:
        total = df[key_metric_col].sum()
        cards.append({"label": f"Total {key_metric_col}", "value": round(float(total), 2)})

    return cards


def _time_series_chart(df: pd.DataFrame) -> dict | None:
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
        return None

    numeric_cols = df.select_dtypes(include=[np.number]).columns
    if len(numeric_cols) == 0:
        return None

    value_col = numeric_cols[0]
    dates = pd.to_datetime(df[date_col], errors="coerce")
    temp = pd.DataFrame({"_date": dates, "_val": df[value_col]}).dropna()
    if temp.empty:
        return None

    temp["_period"] = temp["_date"].dt.to_period("M").astype(str)
    monthly = temp.groupby("_period")["_val"].sum().sort_index()

    return {
        "value_column": value_col,
        "date_column": date_col,
        "data": [{"period": p, "value": round(float(v), 2)} for p, v in monthly.items()],
    }


def generate_dashboard(df: pd.DataFrame, quality_score: float | None, domain: str | None, trained_model_info: dict | None) -> dict:
    numeric_cols = df.select_dtypes(include=[np.number]).columns.tolist()

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

    categorical_cols = [c for c in df.columns if c not in numeric_cols and c != date_col][:4]

    histograms = {col: _numeric_histogram(df[col]) for col in numeric_cols[:6]}
    bar_charts = {col: _top_categories(df[col]) for col in categorical_cols}

    dashboard = {
        "domain": domain,
        "kpi_cards": _kpi_cards(df, quality_score, domain),
        "missing_value_chart": _missing_value_chart(df),
        "correlation_heatmap": compute_correlations(df)["matrix"],
        "histograms": histograms,
        "bar_charts": bar_charts,
        "time_series": _time_series_chart(df),
        "trends": detect_trends(df),
        "feature_importance": (trained_model_info or {}).get("feature_importance"),
    }
    return dashboard
