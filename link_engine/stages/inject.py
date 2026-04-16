import re
import shutil
from datetime import datetime
from pathlib import Path
from hashlib import md5

import frontmatter

from link_engine.db.models import Anchor, Injection, Error
from link_engine.config import get_config


def _is_inside_code_block(text: str, pos: int) -> bool:
    """Check if position is inside a fenced code block."""
    before = text[:pos]
    fence_count = before.count("```")
    return fence_count % 2 == 1


def _is_inside_link(text: str, pos: int) -> bool:
    """Check if position is inside an existing markdown link [...](...) ."""
    # Find all existing links
    pattern = re.compile(r'\[([^\]]+)\]\([^)]+\)')
    for m in pattern.finditer(text):
        if m.start() <= pos <= m.end():
            return True
    return False


def _slugify(text: str) -> str:
    if not text:
        return ""
    text = text.lower().strip()
    text = re.sub(r'[^\w\s-]', '', text)
    text = re.sub(r'[\s_-]+', '-', text)
    return text.strip('-')


def inject_approved_links(approved_anchors, session, run_id: str, dry_run: bool = False) -> dict:
    """
    Inject all approved anchors into their source files.
    Processes in reverse offset order to avoid drift.
    """
    cfg = get_config()
    buffer_chars = cfg.get("injection_buffer_chars", 150)

    results = {"injected": 0, "errors": 0, "skipped": 0}

    # Group anchors by source article
    by_article = {}
    for anchor in approved_anchors:
        article_id = anchor.match.source_chunk.article_id
        if article_id not in by_article:
            by_article[article_id] = []
        by_article[article_id].append(anchor)

    for article_id, anchors in by_article.items():
        article = anchors[0].match.source_chunk.article
        file_path = Path(article.file_path)

        # Re-verify file hash (it might have changed since ingest)
        raw = file_path.read_text(encoding="utf-8")
        post = frontmatter.loads(raw)
        current_hash = md5(post.content.encode()).hexdigest()

        if current_hash != article.content_hash:
            for anchor in anchors:
                _record_error(session, anchor, run_id,
                              "file_changed", "File changed since ingest — aborting injection")
                results["errors"] += 1
            continue

        # Compute frontmatter byte offset (everything before the body)
        # python-frontmatter strips the frontmatter; we need to know how many
        # chars the frontmatter takes in the raw file
        body = post.content
        frontmatter_offset = raw.index(body)

        # Create backup
        backup_path = file_path.with_suffix(".md.bak")
        shutil.copy2(file_path, backup_path)

        try:
            # Sort anchors by char_start DESCENDING (inject back-to-front)
            anchors_sorted = sorted(
                anchors,
                key=lambda a: a.match.source_chunk.char_start,
                reverse=True,
            )

            content = raw  # work on full raw file including frontmatter

            injected_in_file = 0

            for anchor in anchors_sorted:
                chunk = anchor.match.source_chunk
                anchor_text = anchor.edited_anchor or anchor.anchor_text
                target_article = anchor.match.target_chunk.article
                target_heading = anchor.match.target_chunk.heading or ""
                target_url = target_article.url
                target_slug = _slugify(target_heading)
                link_target = f"{target_url}#{target_slug}" if target_slug else target_url

                # Convert body-relative offsets to file-absolute offsets
                abs_start = frontmatter_offset + chunk.char_start
                abs_end = frontmatter_offset + chunk.char_end

                # Search for anchor phrase within chunk's character range
                search_region = content[abs_start:abs_end]
                phrase_pos = search_region.find(anchor_text)

                if phrase_pos == -1:
                    _record_error(session, anchor, run_id,
                                  "phrase_not_found",
                                  f"Anchor phrase '{anchor_text}' not found in chunk")
                    results["errors"] += 1
                    continue

                absolute_pos = abs_start + phrase_pos

                # Safety: buffer from start of file
                if absolute_pos < buffer_chars:
                    _record_error(session, anchor, run_id,
                                  "too_close_to_start", "Injection position within buffer zone")
                    results["skipped"] += 1
                    continue

                # Safety: not inside code block
                if _is_inside_code_block(content, absolute_pos):
                    _record_error(session, anchor, run_id,
                                  "inside_code_block", "Position inside fenced code block")
                    results["skipped"] += 1
                    continue

                # Safety: not inside existing link
                if _is_inside_link(content, absolute_pos):
                    _record_error(session, anchor, run_id,
                                  "inside_existing_link", "Position inside existing markdown link")
                    results["skipped"] += 1
                    continue

                link_md = f"[{anchor_text}]({link_target})"

                if not dry_run:
                    content = (
                        content[:absolute_pos]
                        + link_md
                        + content[absolute_pos + len(anchor_text):]
                    )

                # Record injection
                inj = Injection(
                    anchor_id=anchor.anchor_id,
                    run_id=run_id,
                    status="injected" if not dry_run else "skipped",
                    injected_at=datetime.utcnow() if not dry_run else None,
                    backup_path=str(backup_path),
                )
                session.add(inj)
                injected_in_file += 1
                results["injected"] += 1

            if not dry_run and injected_in_file > 0:
                file_path.write_text(content, encoding="utf-8")

        except Exception as e:
            # Restore backup
            shutil.copy2(backup_path, file_path)
            for anchor in anchors:
                _record_error(session, anchor, run_id, "injection_error", str(e))
                results["errors"] += 1

    session.flush()
    return results


def _record_error(session, anchor, run_id, error_type, message):
    inj = Injection(
        anchor_id=anchor.anchor_id,
        run_id=run_id,
        status="injection_error",
        error_message=message,
    )
    session.add(inj)
    session.add(Error(
        run_id=run_id,
        stage="injection",
        article_id=anchor.match.source_chunk.article_id,
        chunk_id=anchor.match.source_chunk.chunk_id,
        match_id=anchor.match_id,
        error_type=error_type,
        message=message,
        rerun_eligible=True,
    ))