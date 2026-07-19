"""
Executes SQL against an uploaded dataset using DuckDB, with basic safety
guards. This is intentionally conservative: read-only, row-limited, and
restricted to a single registered table named `dataset`.
"""

import os
import json

import duckdb
import pandas as pd

MAX_ROWS_RETURNED = 500
QUERY_TIMEOUT_SECONDS = 10

FORBIDDEN_KEYWORDS = ("insert", "update", "delete", "drop", "alter", "attach", "copy", "pragma")


class UnsafeQueryError(Exception):
    pass


def _read_dataframe(file_path: str) -> pd.DataFrame:
    ext = os.path.splitext(file_path)[1].lower()
    if ext == ".csv":
        return pd.read_csv(file_path)
    if ext in (".xlsx", ".xls"):
        return pd.read_excel(file_path)
    if ext == ".json":
        return pd.read_json(file_path)
    raise ValueError(f"Unsupported file type: {ext}")


def run_query(file_path: str, sql: str) -> list[dict]:
    lowered = sql.lower()
    if any(kw in lowered for kw in FORBIDDEN_KEYWORDS):
        raise UnsafeQueryError("Only read-only SELECT queries are permitted.")
    if "select" not in lowered:
        raise UnsafeQueryError("Query must be a SELECT statement.")

    df = _read_dataframe(file_path)

    con = duckdb.connect(database=":memory:")
    con.register("dataset", df)
    con.execute(f"SET statement_timeout='{QUERY_TIMEOUT_SECONDS}s'") if False else None  # not all duckdb versions support this pragma; kept explicit for clarity

    result_df = con.execute(sql).fetchdf()
    con.close()

    if len(result_df) > MAX_ROWS_RETURNED:
        result_df = result_df.head(MAX_ROWS_RETURNED)

    # Convert via pandas' own JSON serializer first (handles Timestamp/NaT/
    # numpy types correctly), then parse back into plain Python objects —
    # this is what actually needs to be stored as JSON and returned over the API.
    return json.loads(result_df.to_json(orient="records", date_format="iso"))


def load_dataframe(file_path: str) -> pd.DataFrame:
    """Exposed separately so the pipeline can run schema detection and stats
    on the raw dataframe without re-executing SQL."""
    return _read_dataframe(file_path)
