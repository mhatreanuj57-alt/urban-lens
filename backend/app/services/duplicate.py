"""Duplicate detection service."""

from uuid import UUID
from typing import Optional
import logging

logger = logging.getLogger(__name__)


class DuplicateService:
    """Find near-duplicate reports using PostGIS + embeddings."""

    @staticmethod
    async def find_candidates(
        report_id: UUID,
        issue_type: str,
        max_distance_m: float = 100.0,
        max_time_hours: int = 336,  # 14 days
        min_similarity: float = 0.85,
    ) -> list[dict]:
        """Find candidate duplicate reports.

        1. Query PostGIS for reports of same issue_type within distance.
        2. Filter by time window.
        3. Compare embeddings (CLIP/SigLIP) if available.
        """
        # Placeholder — real implementation queries DB + vector store
        logger.info(f"Finding duplicates for report {report_id}")
        return []

    @staticmethod
    async def compute_similarity(
        embedding_a: list[float],
        embedding_b: list[float],
    ) -> float:
        """Cosine similarity between two embeddings."""
        import numpy as np
        a = np.array(embedding_a)
        b = np.array(embedding_b)
        return float(np.dot(a, b) / (np.linalg.norm(a) * np.linalg.norm(b)))


duplicate_service = DuplicateService()
