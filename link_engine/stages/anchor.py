import json
import re
import time
from hashlib import md5

import anthropic

from link_engine.config import get_config
from link_engine.db.models import Anchor, Error, Match

SYSTEM_PROMPT = """You are an expert SEO content strategist for Canvas Homes — a premium Australian custom home builder.

Your task: find the best anchor text to use as an internal link from a SOURCE passage to a TARGET section.

STRICT RULES FOR ANCHOR TEXT:
1. The anchor text MUST be a phrase that exists word-for-word in the SOURCE passage
2. Copy it exactly with the same capitalisation as it appears in the source
3. It must be 3-7 words long
4. It must NOT be generic: never use "learn more", "click here", "read more", "find out", "this guide", "read this", "see here", "more information"
5. It must NOT be identical to the target section heading

WHAT MAKES A HIGH QUALITY LINK (confidence 4-5):
- The target section directly answers a question the source passage raises
- A reader would genuinely benefit from clicking through to learn more
- The anchor phrase is the most natural entry point into the target topic
- The two sections cover complementary aspects of the same subject

WHAT MAKES A LOW QUALITY LINK (confidence 1-2):
- The connection is superficial — both mention homes or building but cover unrelated topics
- The anchor phrase feels forced or out of context
- The reader would not gain anything useful by clicking through

PROCESS:
1. Read the source passage carefully
2. Read the target section heading and content
3. Decide honestly if this is a useful link — if not, set confidence 1 or 2
4. If it IS useful, find the best 3-7 word phrase in the source that leads naturally into the target topic
5. Copy that phrase EXACTLY as it appears in the source text

Respond with a single line of JSON only — no markdown, no explanation outside the JSON:
{"anchor_text": "exact phrase from source", "reasoning": "one sentence explaining reader benefit", "confidence": 4}"""


def compute_anchor_cache_key(source_hash: str, target_hash: str) -> str:
    return md5(f"anchor_v2:{source_hash}:{target_hash}".encode()).hexdigest()


GENERIC_PHRASES = {
    "learn more", "click here", "read this", "find out", "read more",
    "see here", "check this out", "visit here", "go here", "this article",
    "this post", "this page", "this guide", "more information", "find out more",
    "read on", "see more", "learn about", "discover more", "explore more",
    "click to learn", "read further", "learn how",
}


def _is_generic(text: str) -> bool:
    return text.lower().strip() in GENERIC_PHRASES


def _find_phrase_in_source(anchor_text: str, source_text: str) -> str | None:
    """
    Case-insensitive search for anchor phrase in source text.
    Returns the exact matching substring from source (preserving source capitalisation)
    or None if not found.
    """
    idx = source_text.lower().find(anchor_text.lower())
    if idx == -1:
        return None
    # Return the exact substring from source at the same position
    return source_text[idx: idx + len(anchor_text)]


def _validate_anchor(anchor_text: str, target_heading: str, source_text: str, cfg: dict) -> tuple:
    """Returns (is_valid, corrected_anchor_or_None, reason)."""
    words = anchor_text.strip().split()
    min_w = cfg.get("anchor_min_words", 3)
    max_w = cfg.get("anchor_max_words", 7)

    if not (min_w <= len(words) <= max_w):
        return False, None, f"Wrong word count: {len(words)} (need {min_w}-{max_w})"

    if _is_generic(anchor_text):
        return False, None, f"Generic phrase rejected: '{anchor_text}'"

    if target_heading and anchor_text.lower().strip() == target_heading.lower().strip():
        return False, None, f"Anchor identical to heading: '{target_heading}'"

    # Case-insensitive verbatim check — returns source-capitalised version
    found = _find_phrase_in_source(anchor_text, source_text)
    if found is None:
        return False, None, f"Phrase not found in source: '{anchor_text}'"

    # Return the corrected (source-capitalised) anchor text
    return True, found, "ok"


def generate_anchor(match: Match, session, run_id: str = None) -> bool:
    cfg = get_config()
    source_chunk = match.source_chunk
    target_chunk = match.target_chunk

    cache_key = compute_anchor_cache_key(source_chunk.chunk_hash, target_chunk.chunk_hash)

    existing = session.query(Anchor).filter_by(cache_key=cache_key).first()
    if existing:
        existing.match_id = match.match_id
        match.status = "anchor_ready"
        return True

    client = anthropic.Anthropic(api_key=cfg["anthropic_api_key"])
    model = cfg.get("llm_model", "claude-sonnet-4-20250514")
    min_confidence = cfg.get("llm_confidence_threshold", 3)

    user_prompt = f"""SOURCE PASSAGE (this article will contain the outgoing link):
---
{source_chunk.text}
---

TARGET SECTION (this is where the link points):
Section heading: {target_chunk.heading or "Introduction"}
Article: {target_chunk.article.title if target_chunk.article else ""}
---
{target_chunk.text}
---

Find a 3-7 word phrase that exists verbatim in the SOURCE PASSAGE above and works as anchor text pointing to the target section. Copy the phrase exactly as it appears in the source, including capitalisation."""

    last_error = None
    feedback = ""

    for attempt in range(3):
        try:
            full_prompt = user_prompt + feedback

            response = client.messages.create(
                model=model,
                max_tokens=300,
                system=SYSTEM_PROMPT,
                messages=[{"role": "user", "content": full_prompt}],
            )
            raw = response.content[0].text.strip()

            # Strip accidental markdown fences
            if raw.startswith("```"):
                raw = raw.split("\n", 1)[-1].rsplit("```", 1)[0].strip()

            data = json.loads(raw)
            anchor_text = data.get("anchor_text", "").strip()
            reasoning = data.get("reasoning", "")
            confidence = int(data.get("confidence", 1))

            is_valid, corrected, reason = _validate_anchor(
                anchor_text, target_chunk.heading, source_chunk.text, cfg
            )

            if not is_valid:
                feedback = f"\n\nAttempt {attempt+1} failed: {reason}. Please try a different phrase from the source passage."
                if attempt < 2:
                    time.sleep(1)
                    continue
                raise ValueError(f"Validation failed after 3 attempts: {reason}")

            # Use source-capitalised version
            final_anchor = corrected or anchor_text

            # Low confidence — filter out silently
            if confidence < min_confidence:
                match.status = "anchor_error"
                session.add(Error(
                    run_id=run_id,
                    stage="anchor",
                    article_id=source_chunk.article_id,
                    chunk_id=source_chunk.chunk_id,
                    match_id=match.match_id,
                    error_type="low_confidence",
                    message=f"Confidence {confidence} below threshold {min_confidence}: {reasoning}",
                    rerun_eligible=False,
                ))
                return False

            anchor = Anchor(
                match_id=match.match_id,
                anchor_text=final_anchor,
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
    matches = session.query(Match).filter_by(status="pending_anchor").all()
    results = {"success": 0, "errors": 0}

    for match in matches:
        if not match.source_chunk or not match.target_chunk:
            continue
        if generate_anchor(match, session, run_id):
            results["success"] += 1
        else:
            results["errors"] += 1

    session.flush()
    return results