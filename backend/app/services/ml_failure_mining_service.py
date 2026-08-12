from __future__ import annotations

from pathlib import Path
from typing import Any

import joblib
import numpy as np
from sklearn.cluster import KMeans
from sklearn.metrics import silhouette_score

from app.core.config import settings
from app.models.service_ticket import ServiceTicket
from app.models.taxonomy import Cluster


class MLFailureMiningService:
    """
    Adapter around the ML team's unsupervised failure-mining pipeline.

    Pipeline:
        symptom_text + fix_text
            -> PII sanitization
            -> SentenceTransformer (all-MiniLM-L6-v2 by default)
            -> KMeans

    Ground-truth labels are deliberately NOT used as KMeans features.
    """

    def __init__(self) -> None:
        self.model_name = settings.ML_EMBEDDING_MODEL
        self.n_clusters = settings.ML_N_CLUSTERS
        self.artifact_dir = Path(settings.ML_ARTIFACT_DIR)
        self.model_path = self.artifact_dir / "kmeans.joblib"
        self.metadata_path = self.artifact_dir / "ml_metadata.joblib"
        self._embedder = None
        self._kmeans: KMeans | None = None
        self._metadata: dict[str, Any] = {}

        if settings.ML_AUTO_LOAD and self.model_path.exists():
            self.load()

    @property
    def is_fitted(self) -> bool:
        return self._kmeans is not None

    def _get_embedder(self):
        # Lazy import/load keeps normal API startup independent of the ML model.
        if self._embedder is None:
            from sentence_transformers import SentenceTransformer
            self._embedder = SentenceTransformer(self.model_name)
        return self._embedder

    @staticmethod
    def sanitize_text(text: Any) -> str:
        import re

        if text is None:
            return ""
        text = str(text)
        text = re.sub(
            r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}\b",
            "[EMAIL]",
            text,
        )
        text = re.sub(r"\b(?:\+?\d[\d\s\-]{8,}\d)\b", "[PHONE]", text)
        return re.sub(r"\s+", " ", text).strip()

    @classmethod
    def build_combined_text(cls, symptom_text: str | None, fix_text: str | None) -> str:
        symptom = cls.sanitize_text(symptom_text)
        fix = cls.sanitize_text(fix_text)
        return f"SYMPTOM: {symptom} FIX: {fix}".strip()

    def encode(self, texts: list[str]) -> np.ndarray:
        return self._get_embedder().encode(
            texts,
            show_progress_bar=False,
            batch_size=32,
            convert_to_numpy=True,
        )

    def train(self, tickets: list[ServiceTicket]) -> dict[str, Any]:
        usable = [
            ticket
            for ticket in tickets
            if self.sanitize_text(ticket.symptom_text)
            and self.sanitize_text(ticket.fix_text)
        ]

        # Match the ML team's duplicate-removal rule: duplicate symptom/fix
        # pairs do not contribute additional clustering evidence.
        deduped: dict[tuple[str, str], ServiceTicket] = {}
        for ticket in usable:
            key = (
                self.sanitize_text(ticket.symptom_text),
                self.sanitize_text(ticket.fix_text),
            )
            deduped.setdefault(key, ticket)
        usable = list(deduped.values())

        if len(usable) < max(2, self.n_clusters):
            raise ValueError(
                f"Need at least {max(2, self.n_clusters)} unique tickets with symptom and fix text; "
                f"found {len(usable)}."
            )

        texts = [
            self.build_combined_text(ticket.symptom_text, ticket.fix_text)
            for ticket in usable
        ]
        embeddings = self.encode(texts)

        # K cannot exceed records - 1 because silhouette needs at least two
        # populated clusters and is useful as a training diagnostic.
        k = min(self.n_clusters, len(usable) - 1)
        self._kmeans = KMeans(n_clusters=k, random_state=42, n_init=10)
        labels = self._kmeans.fit_predict(embeddings)

        silhouette = None
        if len(set(labels)) > 1 and len(usable) > len(set(labels)):
            silhouette = float(silhouette_score(embeddings, labels))

        profiles: dict[int, dict[str, Any]] = {}
        for cluster_id in sorted(set(labels)):
            members = [
                ticket
                for ticket, label in zip(usable, labels)
                if label == cluster_id
            ]
            profiles[int(cluster_id)] = {
                "size": len(members),
                "examples": [
                    self.build_combined_text(t.symptom_text, t.fix_text)
                    for t in members[:10]
                ],
            }

        self._metadata = {
            "embedding_model": self.model_name,
            "n_clusters": k,
            "records": len(usable),
            "silhouette": silhouette,
            "profiles": profiles,
        }
        self._save()

        return {
            "records": len(usable),
            "embedding_dimensions": int(embeddings.shape[1]),
            "n_clusters": k,
            "cluster_sizes": {
                str(cluster_id): int(sum(label == cluster_id for label in labels))
                for cluster_id in sorted(set(labels))
            },
            "silhouette": silhouette,
        }

    def _save(self) -> None:
        self.artifact_dir.mkdir(parents=True, exist_ok=True)
        joblib.dump(self._kmeans, self.model_path)
        joblib.dump(self._metadata, self.metadata_path)

    def load(self) -> None:
        self._kmeans = joblib.load(self.model_path)
        if self.metadata_path.exists():
            self._metadata = joblib.load(self.metadata_path)

    def predict(self, ticket: ServiceTicket) -> dict[str, Any]:
        if not self.is_fitted:
            raise RuntimeError(
                "ML clustering model is not trained. Call the ML train endpoint first."
            )

        text = self.build_combined_text(ticket.symptom_text, ticket.fix_text)
        embedding = self.encode([text])
        cluster_id = int(self._kmeans.predict(embedding)[0])
        distances = self._kmeans.transform(embedding)[0]
        distance = float(distances[cluster_id])
        profile = self._metadata.get("profiles", {}).get(cluster_id, {})

        # KMeans does not produce calibrated probabilities. Preserve the
        # centroid distance as the model signal instead of inventing a score.
        return {
            "model_name": "sentence-transformer-kmeans",
            "model_version": "v1",
            "cluster_id": cluster_id,
            "distance_to_centroid": distance,
            "failure_mode": None,
            "component": None,
            "department": None,
            "confidence": None,
            "suggested_action": None,
            "cluster_profile": profile,
        }

    def ensure_cluster_record(self, db, cluster_id: int) -> Cluster:
        cluster = db.query(Cluster).filter(
            Cluster.cluster_id_source == "GENERATED",
            Cluster.cluster_label == f"ML_CLUSTER_{cluster_id}",
        ).first()
        if cluster:
            return cluster

        cluster = Cluster(
            cluster_label=f"ML_CLUSTER_{cluster_id}",
            cluster_id_source="GENERATED",
            description="SentenceTransformer + KMeans failure-theme cluster",
        )
        db.add(cluster)
        db.flush()
        return cluster
