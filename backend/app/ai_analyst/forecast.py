"""
A deliberately simple forecasting method — linear trend extrapolation —
used by the LangGraph "forecast" branch. This is intentionally NOT the
full Prophet/XGBoost ML module (that's a separate, heavier pipeline);
this exists so the agentic graph has a real, working alternate path to
route to when a question implies prediction rather than diagnosis,
without requiring the full ML module to be built first.
"""

import numpy as np
import pandas as pd


def simple_linear_forecast(df: pd.DataFrame, date_col: str, value_col: str) -> dict | None:
    working = df[[date_col, value_col]].dropna()
    if working.empty:
        return None

    try:
        working[date_col] = pd.to_datetime(working[date_col])
    except Exception:
        return None

    working["_period"] = working[date_col].dt.to_period("M")
    monthly = working.groupby("_period")[value_col].sum().sort_index()

    if len(monthly) < 3:
        return None  # not enough periods for a trend line to mean anything

    x = np.arange(len(monthly))
    y = monthly.values

    slope, intercept = np.polyfit(x, y, 1)
    predicted_next = float(slope * len(monthly) + intercept)

    # R^2 as a rough fit-quality signal
    y_pred = slope * x + intercept
    ss_res = np.sum((y - y_pred) ** 2)
    ss_tot = np.sum((y - y.mean()) ** 2)
    r_squared = float(1 - ss_res / ss_tot) if ss_tot != 0 else 0.0

    next_period = monthly.index[-1] + 1

    return {
        "method": "linear_trend_extrapolation",
        "periods_used": len(monthly),
        "next_period": str(next_period),
        "predicted_value": round(predicted_next, 2),
        "trend_slope_per_period": round(float(slope), 2),
        "r_squared": round(r_squared, 3),
        "history": [{"period": str(p), "value": round(float(v), 2)} for p, v in monthly.items()],
    }
