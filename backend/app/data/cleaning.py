"""
Auto-cleaning engine.

Builds directly on the profiling engine's findings rather than re-scanning
the data blind. Follows the same principle stated in the profiling module:
never silently make a judgment call that could hide a real problem.

Rules (deliberately conservative, documented so they're defensible):
- Numeric column, missing < 30%  -> impute with median
- Numeric column, missing >= 30% -> leave as-is, flag for manual review
  (imputing a third-plus of a column invents too much data to trust)
- Categorical column, any missing -> impute with mode, or "Unknown" if no
  mode exists (all-null column)
- Duplicate rows -> dropped, keeping the first occurrence
- Numeric outliers -> capped at the IQR bounds (winsorized), never deleted,
  since deleting rows loses potentially-legitimate variation
- Object columns that are actually numeric/date (e.g. "1,200" or "2026-01-05"
  stored as text) -> coerced to the correct type where it can be done safely
- Categorical columns -> label-encoded into a companion `<col>_encoded`
  column, keeping the original for readability
"""

import pandas as pd
import numpy as np


def _is_text_dtype(series: pd.Series) -> bool:
    """
    pandas 2.x/3.x may store plain string columns as legacy `object` dtype
    or the newer `StringDtype` depending on version/config — a plain
    `dtype == object` check silently misses the latter. This checks both.
    """
    return pd.api.types.is_object_dtype(series) or pd.api.types.is_string_dtype(series)


def _try_parse_as_date(series: pd.Series) -> pd.Series | None:
    try:
        parsed = pd.to_datetime(series, errors="coerce", format="mixed")
        # Only accept the conversion if it didn't turn most values into NaT
        if parsed.notna().sum() >= len(series) * 0.8:
            return parsed
    except Exception:
        pass
    return None


def _try_parse_as_numeric(series: pd.Series) -> pd.Series | None:
    cleaned = series.astype(str).str.replace(",", "", regex=False).str.strip()
    parsed = pd.to_numeric(cleaned, errors="coerce")
    if parsed.notna().sum() >= len(series) * 0.8:
        return parsed
    return None


def auto_clean(df: pd.DataFrame) -> tuple[pd.DataFrame, dict]:
    """
    Returns (cleaned_dataframe, cleaning_report).
    cleaning_report documents exactly what was done to each column, so the
    user can see the cleaning wasn't a black box.
    """
    working = df.copy()
    actions: list[dict] = []
    flagged_for_review: list[str] = []

    before_rows = len(working)

    # --- Step 1: fix obviously mistyped columns (numbers/dates stored as text) ---
    for col in working.columns:
        if not _is_text_dtype(working[col]):
            continue

        as_date = _try_parse_as_date(working[col])
        if as_date is not None:
            working[col] = as_date
            actions.append({"column": col, "action": "converted_to_datetime"})
            continue

        as_numeric = _try_parse_as_numeric(working[col])
        if as_numeric is not None:
            working[col] = as_numeric
            actions.append({"column": col, "action": "converted_to_numeric"})

    # --- Step 2: drop exact duplicate rows ---
    duplicate_count = int(working.duplicated().sum())
    if duplicate_count > 0:
        working = working.drop_duplicates(keep="first").reset_index(drop=True)
        actions.append({"column": None, "action": "dropped_duplicate_rows", "count": duplicate_count})

    # --- Step 3: handle missing values + outliers per column ---
    for col in working.columns:
        series = working[col]
        missing_pct = series.isna().sum() / len(series) * 100 if len(series) else 0

        if pd.api.types.is_numeric_dtype(series):
            if missing_pct >= 30:
                flagged_for_review.append(col)
                actions.append({"column": col, "action": "flagged_high_missing_not_imputed", "missing_pct": round(missing_pct, 2)})
            elif missing_pct > 0:
                median_val = series.median()
                working[col] = series.fillna(median_val)
                actions.append({"column": col, "action": "imputed_median", "value": round(float(median_val), 4) if pd.notna(median_val) else None})

            # Outlier capping (winsorizing) via IQR, regardless of whether we imputed above
            clean_series = working[col].dropna()
            if len(clean_series) >= 4:
                q1, q3 = clean_series.quantile(0.25), clean_series.quantile(0.75)
                iqr = q3 - q1
                if iqr > 0:
                    lower, upper = q1 - 1.5 * iqr, q3 + 1.5 * iqr
                    n_capped = int(((working[col] < lower) | (working[col] > upper)).sum())
                    if n_capped > 0:
                        working[col] = working[col].clip(lower=lower, upper=upper)
                        actions.append({"column": col, "action": "capped_outliers", "count": n_capped})

        elif pd.api.types.is_datetime64_any_dtype(series):
            if missing_pct > 0:
                actions.append({"column": col, "action": "flagged_missing_dates_not_imputed", "missing_pct": round(missing_pct, 2)})
                flagged_for_review.append(col)

        else:  # categorical / text
            if missing_pct > 0:
                mode_series = series.mode(dropna=True)
                fill_value = mode_series.iloc[0] if len(mode_series) > 0 else "Unknown"
                working[col] = series.fillna(fill_value)
                actions.append({"column": col, "action": "imputed_mode", "value": str(fill_value)})

    # --- Step 4: encode categorical columns (companion column, original kept) ---
    for col in working.columns:
        if _is_text_dtype(working[col]) and working[col].nunique(dropna=True) <= 50:
            codes, uniques = pd.factorize(working[col])
            working[f"{col}_encoded"] = codes
            actions.append({"column": col, "action": "added_encoded_column", "encoded_column": f"{col}_encoded", "categories": len(uniques)})

    report = {
        "rows_before": before_rows,
        "rows_after": len(working),
        "duplicate_rows_removed": duplicate_count,
        "columns_flagged_for_manual_review": flagged_for_review,
        "actions": actions,
    }

    return working, report
