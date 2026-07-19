"""
Real statistical testing. The LLM never decides whether a difference is
"significant" — that's computed here with scipy and passed to the LLM as a
fact to explain, never as something for it to estimate.
"""

import pandas as pd
from scipy import stats


def compare_last_two_periods(df: pd.DataFrame, date_col: str, value_col: str) -> dict | None:
    """
    Groups rows into periods (by month) using date_col, takes the two most
    recent periods with data, and runs an independent two-sample t-test on
    the raw (non-aggregated) values in value_col between those two periods.

    Returns None if there isn't enough data to run a meaningful test.
    """
    working = df[[date_col, value_col]].dropna()
    if working.empty:
        return None

    try:
        working[date_col] = pd.to_datetime(working[date_col])
    except Exception:
        return None

    working["_period"] = working[date_col].dt.to_period("M")
    periods = sorted(working["_period"].unique())
    if len(periods) < 2:
        return None

    latest, prior = periods[-1], periods[-2]
    group_latest = working[working["_period"] == latest][value_col]
    group_prior = working[working["_period"] == prior][value_col]

    if len(group_latest) < 2 or len(group_prior) < 2:
        return None  # not enough samples to compute a meaningful t-test

    t_stat, p_value = stats.ttest_ind(group_latest, group_prior, equal_var=False)

    return {
        "test": "welch_t_test",
        "period_latest": str(latest),
        "period_prior": str(prior),
        "n_latest": int(len(group_latest)),
        "n_prior": int(len(group_prior)),
        "mean_latest": round(float(group_latest.mean()), 2),
        "mean_prior": round(float(group_prior.mean()), 2),
        "pct_change": round(
            float((group_latest.mean() - group_prior.mean()) / group_prior.mean() * 100), 2
        ) if group_prior.mean() != 0 else None,
        "t_statistic": round(float(t_stat), 3),
        "p_value": round(float(p_value), 4),
        "significant_at_0_05": bool(p_value < 0.05),
        "total_periods_available": len(periods),
    }
