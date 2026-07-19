"""
Data profiling engine.

Given a raw dataframe, this module computes:
- per-column missing value percentage
- per-column outlier percentage (IQR method, numeric columns only)
- duplicate row percentage
- an overall data quality score (0-100)

This is intentionally dependency-light (pandas + numpy only) so it can run
synchronously on upload for small/medium files. For large files, this should
be wrapped in a Celery task instead (see Phase 2 notes in the project guide).
"""

import pandas as pd
import numpy as np


def _detect_outlier_pct(series: pd.Series) -> float | None:
    """IQR method: values outside [Q1 - 1.5*IQR, Q3 + 1.5*IQR] are outliers."""
    clean = series.dropna()
    if len(clean) < 4:
        return None  # not enough data to compute quartiles meaningfully

    q1, q3 = clean.quantile(0.25), clean.quantile(0.75)
    iqr = q3 - q1
    if iqr == 0:
        return 0.0  # no spread — nothing can be an "outlier" by this method

    lower, upper = q1 - 1.5 * iqr, q3 + 1.5 * iqr
    outliers = ((clean < lower) | (clean > upper)).sum()
    return round(float(outliers / len(clean) * 100), 2)


def profile_dataframe(df: pd.DataFrame) -> dict:
    row_count = len(df)
    column_count = len(df.columns)
    warnings: list[str] = []

    duplicate_row_pct = round(float(df.duplicated().sum() / row_count * 100), 2) if row_count else 0.0

    columns_profile = []
    quality_penalties = []

    for col in df.columns:
        series = df[col]
        missing_pct = round(float(series.isna().sum() / row_count * 100), 2) if row_count else 0.0
        unique_count = int(series.nunique(dropna=True))
        is_numeric = pd.api.types.is_numeric_dtype(series)

        outlier_pct = _detect_outlier_pct(series) if is_numeric else None

        columns_profile.append({
            "column": col,
            "dtype": str(series.dtype),
            "missing_pct": missing_pct,
            "duplicate_flagged": False,
            "outlier_pct": outlier_pct,
            "unique_count": unique_count,
        })

        # Quality scoring: missingness and outliers both reduce the score.
        # High missingness (>=30%) is weighted more heavily and flagged —
        # this is a column we should NOT silently auto-impute later.
        if missing_pct >= 30:
            quality_penalties.append(missing_pct * 0.6)
            warnings.append(
                f"Column '{col}' is {missing_pct}% missing — too high to safely "
                f"auto-impute. Recommend manual review before cleaning."
            )
        else:
            quality_penalties.append(missing_pct * 0.3)

        if outlier_pct is not None and outlier_pct > 10:
            quality_penalties.append(outlier_pct * 0.2)
            warnings.append(f"Column '{col}' has {outlier_pct}% outliers (IQR method).")

        if unique_count == 1:
            warnings.append(f"Column '{col}' has a single constant value — likely low signal.")

    if duplicate_row_pct > 5:
        quality_penalties.append(duplicate_row_pct * 0.5)
        warnings.append(f"{duplicate_row_pct}% of rows are exact duplicates.")

    # Quality score: start at 100, subtract weighted penalties, floor at 0.
    avg_penalty = sum(quality_penalties) / max(len(quality_penalties), 1)
    quality_score = round(max(0.0, 100.0 - avg_penalty), 2)

    return {
        "row_count": row_count,
        "column_count": column_count,
        "duplicate_row_pct": duplicate_row_pct,
        "quality_score": quality_score,
        "columns": columns_profile,
        "warnings": warnings,
    }
