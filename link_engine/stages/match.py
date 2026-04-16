from hashlib import md5
from typing import List, Dict

import numpy as np

from link_engine.db.models import Chunk, Embedding, Match, Error
from link_engine.config import get_config
from link_engine.stages.embed import bytes_to_vector


def compute_match_hash(source_hash: str, target_hash: str) -> str:
    return md5(f"{source_hash}{target_hash}".encode()).hexdigest()


def compute_matches(session, run_id: str = None) -> int:
    """
    Compute cosine similarity between all chunk embeddings.
    Filters by threshold, top-N, deduplication, and max links per article.
    Returns count of new matches created.
    """
    cfg = get_config()
    threshold = cfg.get("similarity_threshold", 0.75)
    top_n = cfg.get("top_n_matches", 5)
    max_links_per_article = cfg.get("max_links_per_article", 5)

    # Load all embeddings
    embeddings = session.query(Embedding).all()
    if len(embeddings) < 2:
        return 0

    # Build index: chunk_id -> vector, chunk_id -> article_id
    chunk_ids = []
    vectors = []
    chunk_to_article = {}

    for emb in embeddings:
        chunk = session.get(Chunk, emb.chunk_id)
        if chunk is None:
            continue
        vec = bytes_to_vector(emb.vector)
        chunk_ids.append(emb.chunk_id)
        vectors.append(vec)
        chunk_to_article[emb.chunk_id] = chunk.article_id

    if len(vectors) < 2:
        return 0

    # Normalize for cosine similarity
    matrix = np.vstack(vectors).astype(np.float32)
    norms = np.linalg.norm(matrix, axis=1, keepdims=True)
    norms = np.where(norms == 0, 1e-8, norms)
    normalized = matrix / norms
    similarity_matrix = normalized @ normalized.T  # (N x N)

    n = len(chunk_ids)
    new_matches = 0

    # Track how many outbound links per source article
    article_link_count: Dict[str, int] = {}

    # Collect candidates
    candidates = []
    for i in range(n):
        source_id = chunk_ids[i]
        source_article = chunk_to_article[source_id]

        # Get top-N similar chunks for this source
        scores = similarity_matrix[i].copy()
        scores[i] = 0.0  # exclude self

        # Exclude same-article chunks
        for j, cid in enumerate(chunk_ids):
            if chunk_to_article[cid] == source_article:
                scores[j] = 0.0

        # Apply threshold
        scores[scores < threshold] = 0.0

        # Top-N indices
        top_indices = np.argsort(scores)[::-1][:top_n]
        for j in top_indices:
            score = float(scores[j])
            if score == 0.0:
                continue
            candidates.append((source_id, chunk_ids[j], score, source_article))

    # Sort by score descending to prioritize best matches
    candidates.sort(key=lambda x: x[2], reverse=True)

    # Deduplicate: one link per source_article -> target_article pair
    seen_article_pairs = set()

    for source_id, target_id, score, source_article in candidates:
        target_article = chunk_to_article[target_id]
        pair_key = (source_article, target_article)

        if pair_key in seen_article_pairs:
            continue

        # Check max links per article
        if article_link_count.get(source_article, 0) >= max_links_per_article:
            continue

        # Check match cache
        source_chunk = session.get(Chunk, source_id)
        target_chunk = session.get(Chunk, target_id)
        match_hash = compute_match_hash(source_chunk.chunk_hash, target_chunk.chunk_hash)

        existing = session.query(Match).filter_by(match_hash=match_hash).first()
        if existing:
            seen_article_pairs.add(pair_key)
            article_link_count[source_article] = article_link_count.get(source_article, 0) + 1
            continue

        # Check for duplicate pair
        existing_pair = session.query(Match).filter_by(
            source_chunk_id=source_id,
            target_chunk_id=target_id,
        ).first()
        if existing_pair:
            seen_article_pairs.add(pair_key)
            article_link_count[source_article] = article_link_count.get(source_article, 0) + 1
            continue

        match = Match(
            source_chunk_id=source_id,
            target_chunk_id=target_id,
            similarity_score=score,
            match_hash=match_hash,
            status="pending_anchor",
        )
        session.add(match)
        seen_article_pairs.add(pair_key)
        article_link_count[source_article] = article_link_count.get(source_article, 0) + 1
        new_matches += 1

    session.flush()
    return new_matches