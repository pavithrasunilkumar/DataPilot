"""
Automatically builds the RAG context that gets indexed the moment a
dataset is uploaded — schema descriptions per column, and a starter
business glossary based on the detected domain. This is what lets the
AI Analyst answer with dataset-specific grounding from the very first
question, without any manual documentation step.
"""

import pandas as pd

DOMAIN_GLOSSARIES = {
    "retail": {
        "churn": "A customer is considered churned if they have not made a purchase in the trailing 90 days.",
        "basket size": "The average number of distinct items in a single transaction.",
        "repeat purchase rate": "The share of customers who make more than one purchase in a given period.",
    },
    "finance": {
        "revenue": "Total income recognized from sales before any costs are subtracted.",
        "roi": "Return on investment — net gain from an investment divided by its cost.",
        "fraud flag": "A transaction marked for manual review due to anomalous patterns.",
    },
    "healthcare": {
        "readmission": "A patient returning for inpatient care within 30 days of a prior discharge.",
        "patient flow": "The movement of patients through admission, treatment, and discharge stages.",
    },
    "saas": {
        "churn": "A customer who cancels or fails to renew their subscription in a given period.",
        "mrr": "Monthly Recurring Revenue — predictable revenue normalized to a monthly basis.",
        "active user": "A user who has logged in or performed a tracked action within the last 30 days.",
    },
}

DOMAIN_KEYWORDS = {
    "retail": ["sku", "basket", "inventory", "store", "product"],
    "finance": ["revenue", "profit", "roi", "transaction", "fraud"],
    "healthcare": ["patient", "diagnosis", "admission", "discharge"],
    "saas": ["subscription", "mrr", "arr", "signup", "trial"],
}


def detect_domain(df: pd.DataFrame) -> str:
    columns_lower = " ".join(df.columns).lower()
    scores = {
        domain: sum(1 for kw in keywords if kw in columns_lower)
        for domain, keywords in DOMAIN_KEYWORDS.items()
    }
    best_domain = max(scores, key=scores.get)
    return best_domain if scores[best_domain] > 0 else "general"


def build_schema_descriptions(df: pd.DataFrame) -> dict[str, str]:
    descriptions = {}
    for col in df.columns:
        dtype = str(df[col].dtype)
        samples = df[col].dropna().head(3).tolist()
        descriptions[col] = (
            f"Column '{col}' is of type {dtype}. Example values: {samples}."
        )
    return descriptions


def build_starter_glossary(domain: str) -> dict[str, str]:
    return DOMAIN_GLOSSARIES.get(domain, {})
