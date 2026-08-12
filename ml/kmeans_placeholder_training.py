"""
kmeans_placeholder_training.py

PLACEHOLDER / PLAN-B ML MODEL.

The ML team is building their own pipeline/model. This script exists only as
a fallback so the platform has *something* to plug into the
POST /api/v1/service-tickets/{ticket_id}/ml-result endpoint (via ml_adapter.py)
if the primary pipeline is not ready in time.

Approach:
  - Basic KMeans clustering (NOT a failure_mode/component/department classifier).
  - Input fields (exactly as specified): record, date, product_model,
    serial_range, fix_text, symptom_text.
  - Text fields (symptom_text, fix_text) -> TF-IDF vectors.
  - Categorical fields (product_model, serial_range) -> one-hot.
  - date -> numeric (days since epoch), included as a weak signal.
  - "record" (record_id) is an identifier, NOT a feature - excluded from X,
    only carried through for output traceability.
  - ground-truth labels (failure_mode, component, department) are NEVER used
    as inputs - they exist in the dataset for evaluation/comparison only.

Usage:
    python kmeans_placeholder_training.py --input /path/to/FINALDATASET.csv \
        --output ./artifacts --k 6

Outputs:
    artifacts/kmeans_model.joblib      - fitted KMeans + preprocessing pipeline
    artifacts/cluster_assignments.csv  - record_id -> cluster_id
    artifacts/metrics.json             - silhouette score, k, n_samples
"""
import argparse
import json
import os
from datetime import datetime, timezone

import pandas as pd
import numpy as np
from sklearn.compose import ColumnTransformer
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.cluster import KMeans
from sklearn.metrics import silhouette_score
from sklearn.impute import SimpleImputer
import joblib

MANDATORY_INPUT_FIELDS = ["record", "date", "product_model", "serial_range", "fix_text", "symptom_text"]


def load_dataset(path: str) -> pd.DataFrame:
    df = pd.read_csv(path)

    # Dataset uses `record_id`; the model contract calls the field `record`.
    if "record" not in df.columns and "record_id" in df.columns:
        df = df.rename(columns={"record_id": "record"})

    missing = [c for c in MANDATORY_INPUT_FIELDS if c not in df.columns]
    if missing:
        raise ValueError(f"Dataset is missing mandatory input fields: {missing}")

    # Explicitly drop ground-truth label columns from the feature set if present -
    # they must never leak into clustering inputs.
    label_cols = ["failure_mode", "component", "department"]
    df["_date_numeric"] = pd.to_datetime(df["date"], errors="coerce").map(
        lambda d: (d - pd.Timestamp("1970-01-01")).days if pd.notnull(d) else np.nan
    )
    return df


def build_pipeline(k: int) -> Pipeline:
    text_symptom = TfidfVectorizer(max_features=300, stop_words="english")
    text_fix = TfidfVectorizer(max_features=150, stop_words="english")

    categorical = Pipeline([
        ("impute", SimpleImputer(strategy="most_frequent")),
        ("onehot", OneHotEncoder(handle_unknown="ignore")),
    ])
    numeric = Pipeline([
        ("impute", SimpleImputer(strategy="median")),
        ("scale", StandardScaler()),
    ])

    preprocessor = ColumnTransformer(transformers=[
        ("symptom_tfidf", text_symptom, "symptom_text"),
        ("fix_tfidf", text_fix, "fix_text"),
        ("categorical", categorical, ["product_model", "serial_range"]),
        ("numeric", numeric, ["_date_numeric"]),
    ])

    model = KMeans(n_clusters=k, random_state=42, n_init=10)

    return Pipeline([("preprocess", preprocessor), ("kmeans", model)])


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", required=True, help="Path to FINALDATASET.csv")
    parser.add_argument("--output", default="./artifacts", help="Output directory")
    parser.add_argument("--k", type=int, default=6, help="Number of clusters (dataset currently has 6 cluster IDs)")
    args = parser.parse_args()

    os.makedirs(args.output, exist_ok=True)

    df = load_dataset(args.input)
    df["fix_text"] = df["fix_text"].fillna("")
    df["symptom_text"] = df["symptom_text"].fillna("")

    feature_df = df[["symptom_text", "fix_text", "product_model", "serial_range", "_date_numeric"]]

    pipeline = build_pipeline(args.k)
    pipeline.fit(feature_df)

    transformed = pipeline.named_steps["preprocess"].transform(feature_df)
    labels = pipeline.named_steps["kmeans"].labels_

    # Silhouette score can be expensive on large sparse matrices; sample if large.
    sample_size = min(2000, transformed.shape[0])
    try:
        score = silhouette_score(transformed, labels, sample_size=sample_size, random_state=42)
    except Exception as e:  # e.g. single-cluster degenerate case
        score = None

    joblib.dump(pipeline, os.path.join(args.output, "kmeans_model.joblib"))

    out = pd.DataFrame({"record": df["record"], "cluster_id": labels})
    out.to_csv(os.path.join(args.output, "cluster_assignments.csv"), index=False)

    metrics = {
        "k": args.k,
        "n_samples": int(len(df)),
        "silhouette_score": float(score) if score is not None else None,
        "trained_at": datetime.now(timezone.utc).isoformat(),
        "note": "Placeholder KMeans model. Train/validation/test split (70/15/15) "
                "applies to the eventual supervised failure_mode/component/department "
                "model, not to this unsupervised clustering placeholder.",
    }
    with open(os.path.join(args.output, "metrics.json"), "w") as f:
        json.dump(metrics, f, indent=2)

    print(f"Trained KMeans (k={args.k}) on {len(df)} records.")
    print(f"Silhouette score: {metrics['silhouette_score']}")
    print(f"Artifacts written to: {args.output}")


if __name__ == "__main__":
    main()
