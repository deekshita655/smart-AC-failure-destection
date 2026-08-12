from sqlalchemy import Column, Integer, String
from app.core.database import Base


class FailureMode(Base):
    __tablename__ = "failure_modes"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(128), unique=True, nullable=False)


class Component(Base):
    __tablename__ = "components"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(128), unique=True, nullable=False)


class Department(Base):
    __tablename__ = "departments"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(64), unique=True, nullable=False)


class Cluster(Base):
    """
    Clustering output (from the embedding + KMeans pipeline, or the placeholder
    ML script). cluster_id_source distinguishes dataset-provided cluster_id
    (historical) from newly backend-generated clusters.
    """
    __tablename__ = "clusters"
    id = Column(Integer, primary_key=True, index=True)
    cluster_label = Column(String(128), nullable=True)
    cluster_id_source = Column(String(32), default="GENERATED", nullable=False)  # DATASET | GENERATED
    description = Column(String(512), nullable=True)
