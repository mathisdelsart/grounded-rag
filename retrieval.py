"""Query-side retrieval.

Embeds the question with the same model used at indexing time, fetches the
top-k most similar chunks from Qdrant, and applies the similarity threshold.
An empty result means nothing in the course is relevant enough, which the
answer layer turns into an explicit refusal rather than a guess.
"""

from qdrant_client import QdrantClient

from config import get_settings
from ingestion.embed import embed_query
from ingestion.schema import Chunk, Retrieved


def retrieve(question: str, *, k: int = 5) -> list[Retrieved]:
    """Return up to k chunks above the similarity threshold, best first."""
    settings = get_settings()
    client = QdrantClient(url=settings.qdrant_url)

    response = client.query_points(
        collection_name=settings.qdrant_collection,
        query=embed_query(question),
        limit=k,
        score_threshold=settings.similarity_threshold,
        with_payload=True,
    )

    results: list[Retrieved] = []
    for point in response.points:
        payload = point.payload or {}
        chunk = Chunk(
            id=str(point.id),
            course=payload["course"],
            page=payload["page"],
            text=payload["text"],
            chapter=payload.get("chapter"),
        )
        results.append(Retrieved(chunk=chunk, score=point.score))
    return results
