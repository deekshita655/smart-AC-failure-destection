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
    def __init__(self) -> None:
        self.model_name = getattr(settings, "ML_EMBEDDING_MODEL", "all-MiniLM-L6-v2")
        self.n_clusters = getattr(settings, "ML_N_CLUSTERS", 5)
        self.artifact_dir = Path(getattr(settings, "ML_ARTIFACT_DIR", "ml_artifacts"))
        self.model_path = self.artifact_dir / "kmeans.joblib"
        self.metadata_path = self.artifact_dir / "ml_metadata.joblib"
        self._embedder = None
        self._kmeans: KMeans | None = None
        self._metadata: dict[str, Any] = {}
        if self.model_path.exists(): self.load()

    @property
    def is_fitted(self) -> bool: return self._kmeans is not None

    def _get_embedder(self):
        if self._embedder is None:
            from sentence_transformers import SentenceTransformer
            self._embedder = SentenceTransformer(self.model_name)
        return self._embedder

    @staticmethod
    def sanitize_text(text: Any) -> str:
        import re
        if text is None: return ""
        text = re.sub(r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}\b", "[EMAIL]", str(text))
        text = re.sub(r"\b(?:\+?\d[\d\s\-]{8,}\d)\b", "[PHONE]", text)
        return re.sub(r"\s+", " ", text).strip()

    @classmethod
    def build_combined_text(cls, symptom_text, fix_text):
        return f"SYMPTOM: {cls.sanitize_text(symptom_text)} FIX: {cls.sanitize_text(fix_text)}".strip()

    def encode(self, texts: list[str]) -> np.ndarray:
        return self._get_embedder().encode(texts, show_progress_bar=False, batch_size=32, convert_to_numpy=True)

    def train(self, tickets: list[ServiceTicket]) -> dict[str, Any]:
        usable = [t for t in tickets if self.sanitize_text(t.symptom_text) and self.sanitize_text(t.fix_text)]
        deduped = {}
        for t in usable:
            deduped.setdefault((self.sanitize_text(t.symptom_text), self.sanitize_text(t.fix_text)), t)
        usable = list(deduped.values())
        if len(usable) < max(2, self.n_clusters):
            raise ValueError(f"Need at least {max(2, self.n_clusters)} unique tickets with symptom and fix text; found {len(usable)}.")
        embeddings = self.encode([self.build_combined_text(t.symptom_text, t.fix_text) for t in usable])
        k = min(self.n_clusters, len(usable) - 1)
        self._kmeans = KMeans(n_clusters=k, random_state=42, n_init=10)
        labels = self._kmeans.fit_predict(embeddings)
        silhouette = float(silhouette_score(embeddings, labels)) if len(set(labels)) > 1 and len(usable) > len(set(labels)) else None
        profiles = {}
        for cid in sorted(set(labels)):
            members = [t for t, label in zip(usable, labels) if label == cid]
            profiles[int(cid)] = {"size": len(members), "examples": [self.build_combined_text(t.symptom_text, t.fix_text) for t in members[:10]]}
        self._metadata = {"embedding_model": self.model_name, "n_clusters": k, "records": len(usable), "silhouette": silhouette, "profiles": profiles}
        self._save()
        return {"records": len(usable), "embedding_dimensions": int(embeddings.shape[1]), "n_clusters": k,
                "cluster_sizes": {str(cid): int(sum(label == cid for label in labels)) for cid in sorted(set(labels))}, "silhouette": silhouette}

    def _save(self):
        self.artifact_dir.mkdir(parents=True, exist_ok=True)
        joblib.dump(self._kmeans, self.model_path); joblib.dump(self._metadata, self.metadata_path)

    def load(self):
        self._kmeans = joblib.load(self.model_path)
        if self.metadata_path.exists(): self._metadata = joblib.load(self.metadata_path)

    def predict(self, ticket: ServiceTicket) -> dict[str, Any]:
        if not self.is_fitted: raise RuntimeError("ML clustering model is not trained. Call the ML train endpoint first.")
        embedding = self.encode([self.build_combined_text(ticket.symptom_text, ticket.fix_text)])
        cid = int(self._kmeans.predict(embedding)[0]); distance = float(self._kmeans.transform(embedding)[0][cid])
        return {"model_name":"sentence-transformer-kmeans", "model_version":"v1", "cluster_id":cid,
                "distance_to_centroid":distance, "cluster_profile":self._metadata.get("profiles",{}).get(cid,{})}

    def ensure_cluster_record(self, db, cluster_id: int) -> Cluster:
        cluster = db.query(Cluster).filter(Cluster.cluster_id_source == "GENERATED", Cluster.cluster_label == f"ML_CLUSTER_{cluster_id}").first()
        if cluster: return cluster
        cluster = Cluster(cluster_label=f"ML_CLUSTER_{cluster_id}", cluster_id_source="GENERATED", description="SentenceTransformer + KMeans failure-theme cluster")
        db.add(cluster); db.flush(); return cluster
