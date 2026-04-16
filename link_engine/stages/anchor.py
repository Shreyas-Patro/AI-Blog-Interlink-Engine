import json
import time
from hashlib import md5

import anthropic

from link_engine.config import get_config
from link_engine.db.models import Anchor, Error, Match

SYSTEM_PROMPT = """You are an expert SEO strategist writing internal link anchor text.

Given a SOURCE passage and a TARGET passage, select anchor text that:
- Is EXACTLY 3-6 words long
- Appears naturally in the source passage as a readable phrase
- Is NOT generic (never use: learn more, click here, read this, find out, read more, see here)
- Is NOT identical to the target section heading
- Reflects the specific topic of the target section
- Would make sense as clickable link text in context

Respond ONLY with valid JSON on a single line, no markdown, no explanation outside JSON:
{"anchor_text": "your chosen phrase", "reasoning": "brief explanation", "confidence": 4}

confidence is 1-5 where:
1 = poor fit, 2 = weak, 3 = acceptable, 4 = good, 5 = perfect natural fit"""


def compute_anchor_cache_key(source_hash: str, target_hash: str) -> str:
    return md5(f"anchor:{source_hash}:{target_hash}".encode()).hexdigest()


GENERIC_PHRASES = {
    "learn more", "click here", "read this", "find out", "read more",
    "see here", "check this out", "visit here", "go here", "this article",
    "this post", "this page", "this guide", "more information",
}


def _is_generic(text: str) -> bool:
    return text.lower().strip() in GENERIC_PHRASES


def _validate_anchor(anchor_text: str, target_heading: str, cfg: dict) -> bool:
    words = anchor_text.strip().split()
    min_w = cfg.get("anchor_min_words", 3)
    max_w = cfg.get("anchor_max_words", 6)
    if not (min_w <= len(words) <= max_w):
        return False
    if _is_generic(anchor_text):
        return False
    if target_heading and anchor_text.lower().strip() == target_heading.lower().strip():
        return False
    return True


def generate_anchor(match: Match, session, run_id: str = None) -> bool:
    """
    Generate anchor text for a match. Returns True on success.
    Uses cache keyed on (source_chunk_hash, target_chunk_hash).
    """
    cfg = get_config()
    source_chunk = match.source_chunk
    target_chunk = match.target_chunk

    cache_key = compute_anchor_cache_key(source_chunk.chunk_hash, target_chunk.chunk_hash)

    # Check cache
    existing = session.query(Anchor).filter_by(cache_key=cache_key).first()
    if existing:
        existing.match_id = match.match_id  # update match reference
        match.status = "anchor_ready"
        return True

    client = anthropic.Anthropic(api_key=cfg["anthropic_api_key"])
    model = cfg.get("llm_model", "claude-sonnet-4-20250514")

    user_prompt = f"""SOURCE PASSAGE:
{source_chunk.text}

TARGET SECTION HEADING: {target_chunk.heading or "Introduction"}
TARGET PASSAGE:
{target_chunk.text}

Choose anchor text that exists as a natural phrase in the SOURCE PASSAGE."""

    # Retry up to 2 times
    last_error = None
    for attempt in range(3):
        try:
            response = client.messages.create(
                model=model,
                max_tokens=200,
                system=SYSTEM_PROMPT,
                messages=[{"role": "user", "content": user_prompt}],
            )
            raw = response.content[0].text.strip()

            # Parse JSON
            data = json.loads(raw)
            anchor_text = data.get("anchor_text", "").strip()
            reasoning = data.get("reasoning", "")
            confidence = int(data.get("confidence", 3))

            # Validate
            if not _validate_anchor(anchor_text, target_chunk.heading, cfg):
                if attempt < 2:
                    time.sleep(1)
                    continue
                raise ValueError(f"Anchor validation failed: '{anchor_text}'")

            # Store
            anchor = Anchor(
                match_id=match.match_id,
                anchor_text=anchor_text,
                reasoning=reasoning,
                llm_confidence=confidence,
                model=model,
                cache_key=cache_key,
                status="pending_review",
            )
            session.add(anchor)
            match.status = "anchor_ready"
            return True

        except Exception as e:
            last_error = e
            if attempt < 2:
                time.sleep(2 ** attempt)

    # All retries failed
    match.status = "anchor_error"
    session.add(Error(
        run_id=run_id,
        stage="anchor",
        article_id=source_chunk.article_id,
        chunk_id=source_chunk.chunk_id,
        match_id=match.match_id,
        error_type="anchor_error",
        message=str(last_error),
        rerun_eligible=True,
    ))
    return False


def generate_all_anchors(session, run_id: str = None) -> dict:
    """Generate anchors for all pending_anchor matches."""
    matches = session.query(Match).filter_by(status="pending_anchor").all()
    results = {"success": 0, "cached": 0, "errors": 0}

    for match in matches:
        if not match.source_chunk or not match.target_chunk:
            continue
        success = generate_anchor(match, session, run_id)
        if success:
            results["success"] += 1
        else:
            results["errors"] += 1

    session.flush()
    return results