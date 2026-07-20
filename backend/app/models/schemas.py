from pydantic import BaseModel
from typing import Optional


class ClusterRequest(BaseModel):
    texts: list[str]
    n_clusters: Optional[int] = None
    method: str = "kmeans"  # "kmeans" for manual/specified clusters, "hdbscan" for auto-detect
    min_cluster_size: Optional[int] = None  # Only used for HDBSCAN method


class ClusterPoint(BaseModel):
    x: float
    y: float
    cluster: str
    confidence: float
    text: str


class ClusterInfo(BaseModel):
    id: str
    name: str
    description: Optional[str] = None
    size: int
    color: str


class ClusterStats(BaseModel):
    total_points: int
    num_clusters: int
    silhouette_score: float


class ClusterResponse(BaseModel):
    clusters: list[ClusterInfo]
    points: list[ClusterPoint]
    stats: ClusterStats


class SampleTextsResponse(BaseModel):
    texts: list[str]
    count: int  # actual number of texts returned
