import numpy as np
from typing import List

from link_engine.db.models import Chunk, Embedding, Error
from link_engine.config import get_config

# Load model once at module level (takes ~3 seconds on first import)
_model = None


def get_model():
    global _model
    if _model is None:
        from sentence_transformers import SentenceTransformer
        cfg = get_config()
        model_name = cfg.get("embedding_model", "all-MiniLM-L6-v2")
        _model = SentenceTransformer(model_name)
    return _model


def vector_to_bytes(vector: np.ndarray) -> bytes:
    return vector.astype(np.float32).tobytes()


def bytes_to_vector(blob: bytes) -> np.ndarray:
    return np.frombuffer(blob, dtype=np.float32)


def embed_chunks(chunks: List[Chunk], session) -> int:
    """
    Embed all chunks, using cache. Returns count of new embeddings computed.
    """
    cfg = get_config()
    model_name = cfg.get("embedding_model", "all-MiniLM-L6-v2")
    model = get_model()

    # Separate cache hits from misses
    to_embed = []
    for chunk in chunks:
        existing = session.get(Embedding, chunk.chunk_id)
        if existing and existing.chunk_hash == chunk.chunk_hash:
            continue  # Cache hit — skip
        to_embed.append(chunk)

    if not to_embed:
        return 0

    # Batch embedding in groups of 100
    batch_size = 100
    computed = 0

    for i in range(0, len(to_embed), batch_size):
        batch = to_embed[i:i + batch_size]
        texts = [c.text for c in batch]

        try:
            vectors = model.encode(texts, show_progress_bar=False)
            for chunk, vector in zip(batch, vectors):
                blob = vector_to_bytes(vector)
                existing = session.get(Embedding, chunk.chunk_id)
                if existing:
                    existing.vector = blob
                    existing.chunk_hash = chunk.chunk_hash
                    existing.model = model_name
                    existing.dimensions = len(vector)
                else:
                    emb = Embedding(
                        chunk_id=chunk.chunk_id,
                        model=model_name,
                        vector=blob,
                        dimensions=len(vector),
                        chunk_hash=chunk.chunk_hash,
                    )
                    session.add(emb)
                computed += 1
        except Exception as e:
            for chunk in batch:
                session.add(Error(
                    stage="embedding",
                    chunk_id=chunk.chunk_id,
                    article_id=chunk.article_id,
                    error_type="embedding_error",
                    message=str(e),
                    rerun_eligible=True,
                ))

    session.flush()
    return computed


def embed_all_pending(session) -> int:
    """Embed all chunks that have no embedding or stale embedding."""
    from link_engine.db.models import Chunk
    all_chunks = session.query(Chunk).all()
    return embed_chunks(all_chunks, session)