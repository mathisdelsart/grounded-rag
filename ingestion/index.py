"""Embeddings and Qdrant upsert.

Local multilingual embeddings (bge-m3), then upsert {vector, payload} into Qdrant.
The payload stores the chunk text and its metadata for citations.
"""

# TODO: implement index_chunks(chunks) -> None
