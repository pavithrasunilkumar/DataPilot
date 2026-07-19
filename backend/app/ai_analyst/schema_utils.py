"""
Lightweight schema inspection — no LLM needed for this part.
Used both to build the schema description sent to the LLM, and to find
a sensible date column + numeric column pair for the significance test.
"""

import pandas as pd


def describe_schema(df: pd.DataFrame) -> str:
    lines = []
    for col in df.columns:
        dtype = str(df[col].dtype)
        sample = df[col].dropna().head(2).tolist()
        lines.append(f"- {col} ({dtype}), e.g. {sample}")
    return "\n".join(lines)


def guess_date_column(df: pd.DataFrame) -> str | None:
    for col in df.columns:
        lname = col.lower()
        if any(k in lname for k in ("date", "month", "period", "time", "created")):
            return col
    # fallback: try to parse each object column as a date
    for col in df.columns:
        if pd.api.types.is_object_dtype(df[col]) or pd.api.types.is_string_dtype(df[col]):
            try:
                pd.to_datetime(df[col].dropna().head(20))
                return col
            except Exception:
                continue
    return None


def guess_numeric_target_column(df: pd.DataFrame, question: str) -> str | None:
    numeric_cols = [c for c in df.columns if pd.api.types.is_numeric_dtype(df[c])]
    if not numeric_cols:
        return None

    # Prefer a numeric column whose name is actually mentioned in the question
    q = question.lower()
    for col in numeric_cols:
        if col.lower() in q:
            return col

    # Otherwise prefer common business-metric-sounding names
    priority_keywords = ["revenue", "sales", "profit", "amount", "price", "cost", "value"]
    for kw in priority_keywords:
        for col in numeric_cols:
            if kw in col.lower():
                return col

    return numeric_cols[0]


# ---------- Domain detection ----------
# Simple, explainable keyword matching — no ML/LLM needed for this step.
# Each business domain gets a small glossary the RAG layer can inject as
# context, so "churn" or "readmission" mean the right thing for this dataset.

DOMAIN_KEYWORDS: dict[str, list[str]] = {
    "retail": ["sku", "inventory", "basket", "product", "order", "discount", "unit_price", "quantity"],
    "finance": ["revenue", "profit", "roi", "expense", "invoice", "transaction", "fraud", "account"],
    "healthcare": ["patient", "diagnosis", "admission", "readmission", "mortality", "treatment", "clinician"],
    "hr": ["employee", "salary", "attrition", "headcount", "hire_date", "performance_review"],
    "marketing": ["campaign", "impression", "click", "conversion", "lead", "channel", "ctr"],
}

DOMAIN_GLOSSARY: dict[str, dict[str, str]] = {
    "retail": {
        "basket size": "the average number of items or total value per customer transaction",
        "churn": "a customer who has not made a purchase within the business's defined inactivity window",
        "sku": "stock keeping unit — a unique identifier for a distinct product/variant",
    },
    "finance": {
        "roi": "return on investment — net gain divided by the cost of the investment",
        "churn": "a customer or account that has cancelled or lapsed",
        "fraud": "a transaction flagged as inconsistent with the account's normal behavior pattern",
    },
    "healthcare": {
        "readmission": "a patient returning for inpatient care within a defined window (commonly 30 days) after discharge",
        "mortality rate": "the proportion of patients who died within a defined period or cohort",
    },
    "hr": {
        "attrition": "the rate at which employees leave the organization over a given period",
        "headcount": "the total number of active employees at a point in time",
    },
    "marketing": {
        "ctr": "click-through rate — clicks divided by impressions",
        "conversion": "a lead or visitor completing a desired action (e.g. purchase, signup)",
    },
}


def detect_domain(df: pd.DataFrame) -> str:
    columns_lower = " ".join(c.lower() for c in df.columns)
    scores = {
        domain: sum(1 for kw in keywords if kw in columns_lower)
        for domain, keywords in DOMAIN_KEYWORDS.items()
    }
    best_domain = max(scores, key=scores.get)
    return best_domain if scores[best_domain] > 0 else "general"


def get_glossary(domain: str) -> dict[str, str]:
    return DOMAIN_GLOSSARY.get(domain, {})
