from hashlib import md5
from typing import Dict, List

import numpy as np

from link_engine.config import get_config
from link_engine.db.models import Chunk, Embedding, Match, Error
from link_engine.stages.embed import bytes_to_vector


def compute_match_hash(source_hash: str, target_hash: str) -> str:
    return md5(f"{source_hash}{target_hash}".encode()).hexdigest()


def compute_matches(session, run_id: str = None) -> int:
    cfg = get_config()
    threshold = cfg.get("similarity_threshold", 0.52)
    top_n = cfg.get("top_n_matches", 8)
    max_links_per_article = cfg.get("max_links_per_article", 6)

    embeddings = session.query(Embedding).all()
    if len(embeddings) < 2:
        return 0

    chunk_ids = []
    vectors = []
    chunk_to_article = {}
    chunk_to_hash = {}

    for emb in embeddings:
        chunk = session.get(Chunk, emb.chunk_id)
        if chunk is None:
            continue
        vec = bytes_to_vector(emb.vector)
        chunk_ids.append(emb.chunk_id)
        vectors.append(vec)
        chunk_to_article[emb.chunk_id] = chunk.article_id
        chunk_to_hash[emb.chunk_id] = chunk.chunk_hash

    if len(vectors) < 2:
        return 0

    matrix = np.vstack(vectors).astype(np.float32)
    norms = np.linalg.norm(matrix, axis=1, keepdims=True)
    norms = np.where(norms == 0, 1e-8, norms)
    normalized = matrix / norms
    sim_matrix = normalized @ normalized.T

    n = len(chunk_ids)
    new_matches = 0

    # Track outbound link count per source article
    article_link_count: Dict[str, int] = {}

    # Collect all valid candidates
    candidates = []
    for i in range(n):
        source_id = chunk_ids[i]
        source_article = chunk_to_article[source_id]

        scores = sim_matrix[i].copy()
        scores[i] = 0.0  # exclude self

        # Exclude same-article chunks
        for j, cid in enumerate(chunk_ids):
            if chunk_to_article[cid] == source_article:
                scores[j] = 0.0

        # Apply threshold
        scores[scores < threshold] = 0.0

        # Top-N for this source chunk
        top_indices = np.argsort(scores)[::-1][:top_n]
        for j in top_indices:
            score = float(scores[j])
            if score == 0.0:
                continue
            candidates.append((score, source_id, chunk_ids[j]))

    # Sort by score descending — best matches processed first
    candidates.sort(key=lambda x: x[0], reverse=True)

    # Deduplicate at CHUNK level (not article level)
    # One link per source_chunk → target_chunk pair
    seen_chunk_pairs = set()

    for score, source_id, target_id in candidates:
        source_article = chunk_to_article[source_id]

        pair_key = (source_id, target_id)
        if pair_key in seen_chunk_pairs:
            continue

        # Check max outbound links per source article
        if article_link_count.get(source_article, 0) >= max_links_per_article:
            continue

        # Check match cache
        match_hash = compute_match_hash(
            chunk_to_hash[source_id],
            chunk_to_hash[target_id]
        )
        existing = session.query(Match).filter_by(match_hash=match_hash).first()
        if existing:
            seen_chunk_pairs.add(pair_key)
            article_link_count[source_article] = article_link_count.get(source_article, 0) + 1
            continue

        # Check for exact pair duplicate
        existing_pair = session.query(Match).filter_by(
            source_chunk_id=source_id,
            target_chunk_id=target_id,
        ).first()
        if existing_pair:
            seen_chunk_pairs.add(pair_key)
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
        seen_chunk_pairs.add(pair_key)
        article_link_count[source_article] = article_link_count.get(source_article, 0) + 1
        new_matches += 1

    session.flush()
    return new_matches