"""
Skeptic Agent.

Most "AI analyst" tools present their output as confident and final. This
module runs a second pass that actively looks for reasons the conclusion
might be wrong or overstated, using concrete checks wherever possible
(sample size, data history length, variance) rather than just asking an
LLM to "be more skeptical" in prose.

The output is a structured critique, not a vague disclaimer — it's meant
to be shown next to the original explanation, not instead of it.
"""


def critique_insight(stat_test: dict | None, total_row_count: int) -> dict:
    flags = []
    trust_level = "high"

    if stat_test is None:
        flags.append({
            "type": "insufficient_data",
            "severity": "high",
            "message": (
                "Not enough periods of data were available to run a significance test. "
                "This finding is descriptive only — it has not been statistically validated."
            ),
        })
        trust_level = "low"
        return {"flags": flags, "trust_level": trust_level}

    n_latest = stat_test.get("n_latest", 0)
    n_prior = stat_test.get("n_prior", 0)
    p_value = stat_test.get("p_value", 1.0)
    total_periods = stat_test.get("total_periods_available", 0)

    # Small sample size check
    if n_latest < 30 or n_prior < 30:
        flags.append({
            "type": "small_sample_size",
            "severity": "medium",
            "message": (
                f"One or both compared groups are small (n={n_latest} vs n={n_prior}). "
                "With small samples, a t-test can be misleading — a few unusual data points "
                "can swing the result. Treat this as a signal to investigate, not a settled fact."
            ),
        })
        trust_level = _downgrade(trust_level)

    # Seasonality check — not enough history to rule out a recurring yearly pattern
    if total_periods < 13:
        flags.append({
            "type": "insufficient_history_for_seasonality",
            "severity": "medium",
            "message": (
                f"Only {total_periods} period(s) of history are available, which is less than "
                "one full year. This change could be a recurring seasonal pattern rather than "
                "a genuine trend — there isn't enough history yet to rule that out."
            ),
        })
        trust_level = _downgrade(trust_level)

    # Marginal significance check
    if 0.05 <= p_value < 0.10:
        flags.append({
            "type": "marginal_significance",
            "severity": "low",
            "message": (
                f"The result (p = {p_value}) is close to the significance threshold but doesn't "
                "clear it. Worth monitoring next period rather than acting on immediately."
            ),
        })
        trust_level = _downgrade(trust_level)

    # Correlation vs causation reminder — always included, since SQL aggregation
    # can never establish causality by itself.
    flags.append({
        "type": "correlation_not_causation",
        "severity": "info",
        "message": (
            "This analysis shows a statistical association between time period and the metric, "
            "not a proven cause. Other factors that changed at the same time could be the real driver."
        ),
    })

    return {"flags": flags, "trust_level": trust_level}


def _downgrade(current: str) -> str:
    order = ["high", "medium", "low"]
    idx = order.index(current)
    return order[min(idx + 1, len(order) - 1)]
