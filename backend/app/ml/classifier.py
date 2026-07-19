"""
ML classification module.

Given a dataset and a target column, this:
1. Decides the task type (binary/multiclass classification, or flags
   regression as not-yet-supported by this endpoint)
2. Builds features from the remaining columns (numeric columns used as-is,
   categorical columns label-encoded — consistent with the cleaning engine's
   approach so results line up with what the user already saw)
3. Splits train/test, trains a baseline (LogisticRegression) AND a boosted
   model (XGBoost), and reports honest metrics for both rather than only
   showing whichever looks better
4. Explains the chosen (better) model's predictions with SHAP

This deliberately does NOT pretend to auto-detect "the interesting target
column" — the user (or the calling endpoint) specifies it, because picking
a business-meaningful prediction target is a judgment call, not something
that should be silently guessed.
"""

import numpy as np
import pandas as pd
from sklearn.linear_model import LogisticRegression
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score, precision_score, recall_score, f1_score
from sklearn.preprocessing import StandardScaler
import xgboost as xgb
import shap


class UnsupportedTargetError(Exception):
    pass


def _prepare_features(df: pd.DataFrame, target_column: str) -> tuple[pd.DataFrame, list[str]]:
    feature_df = df.drop(columns=[target_column]).copy()
    encoded_columns = []

    for col in feature_df.columns:
        if pd.api.types.is_numeric_dtype(feature_df[col]):
            feature_df[col] = feature_df[col].fillna(feature_df[col].median())
        elif pd.api.types.is_datetime64_any_dtype(feature_df[col]):
            # Turn a raw date into something a model can use: days since the
            # earliest date in the column, rather than dropping it entirely.
            feature_df[col] = (feature_df[col] - feature_df[col].min()).dt.days
            feature_df[col] = feature_df[col].fillna(feature_df[col].median())
        else:
            codes, _ = pd.factorize(feature_df[col])
            feature_df[col] = codes
            encoded_columns.append(col)

    return feature_df, encoded_columns


def train_classifier(df: pd.DataFrame, target_column: str) -> dict:
    if target_column not in df.columns:
        raise UnsupportedTargetError(f"Column '{target_column}' not found in dataset.")

    target = df[target_column]
    n_classes = target.nunique(dropna=True)

    if n_classes < 2:
        raise UnsupportedTargetError(f"Target column '{target_column}' has fewer than 2 distinct values.")
    if n_classes > 10:
        raise UnsupportedTargetError(
            f"Target column '{target_column}' has {n_classes} distinct values — this looks like a "
            "regression or high-cardinality target, which this classifier endpoint doesn't support yet."
        )

    working = df.dropna(subset=[target_column]).copy()
    y, class_labels = pd.factorize(working[target_column])
    X, encoded_columns = _prepare_features(working, target_column)

    if len(working) < 20:
        raise UnsupportedTargetError(
            f"Only {len(working)} usable rows — need at least 20 to train and evaluate a model honestly."
        )

    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42, stratify=y if n_classes > 1 else None
    )

    # --- Baseline model ---
    scaler = StandardScaler()
    X_train_scaled = scaler.fit_transform(X_train)
    X_test_scaled = scaler.transform(X_test)

    baseline = LogisticRegression(max_iter=1000)
    baseline.fit(X_train_scaled, y_train)
    baseline_preds = baseline.predict(X_test_scaled)

    # --- Boosted model ---
    boosted = xgb.XGBClassifier(
        n_estimators=100, max_depth=4, learning_rate=0.1,
        eval_metric="logloss", random_state=42,
    )
    boosted.fit(X_train, y_train)
    boosted_preds = boosted.predict(X_test)

    def _metrics(y_true, y_pred):
        average = "binary" if n_classes == 2 else "macro"
        return {
            "accuracy": round(float(accuracy_score(y_true, y_pred)), 4),
            "precision": round(float(precision_score(y_true, y_pred, average=average, zero_division=0)), 4),
            "recall": round(float(recall_score(y_true, y_pred, average=average, zero_division=0)), 4),
            "f1": round(float(f1_score(y_true, y_pred, average=average, zero_division=0)), 4),
        }

    baseline_metrics = _metrics(y_test, baseline_preds)
    boosted_metrics = _metrics(y_test, boosted_preds)

    chosen = "xgboost" if boosted_metrics["f1"] >= baseline_metrics["f1"] else "logistic_regression"

    # --- SHAP explanation for the chosen model (only supported cleanly for XGBoost here) ---
    feature_importance = []
    if chosen == "xgboost":
        explainer = shap.TreeExplainer(boosted)
        shap_values = explainer.shap_values(X_test)
        # For multiclass, shap_values is a list per class — average abs importance across classes
        if isinstance(shap_values, list):
            abs_mean = np.mean([np.abs(sv).mean(axis=0) for sv in shap_values], axis=0)
        else:
            abs_mean = np.abs(shap_values).mean(axis=0)
        importance_pairs = sorted(zip(X.columns, abs_mean), key=lambda p: p[1], reverse=True)
        feature_importance = [{"feature": f, "importance": round(float(v), 4)} for f, v in importance_pairs]
    else:
        importances = np.abs(baseline.coef_).mean(axis=0) if baseline.coef_.ndim > 1 else np.abs(baseline.coef_[0])
        importance_pairs = sorted(zip(X.columns, importances), key=lambda p: p[1], reverse=True)
        feature_importance = [{"feature": f, "importance": round(float(v), 4)} for f, v in importance_pairs]

    return {
        "task_type": "binary_classification" if n_classes == 2 else "multiclass_classification",
        "target_column": target_column,
        "class_labels": [str(c) for c in class_labels],
        "n_train": len(X_train),
        "n_test": len(X_test),
        "encoded_columns": encoded_columns,
        "baseline_model": {"type": "logistic_regression", "metrics": baseline_metrics},
        "boosted_model": {"type": "xgboost", "metrics": boosted_metrics},
        "chosen_model": chosen,
        "feature_importance": feature_importance[:15],
    }
