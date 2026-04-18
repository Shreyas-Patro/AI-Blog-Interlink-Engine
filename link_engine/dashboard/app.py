import re
import shutil
from datetime import datetime
from pathlib import Path

import frontmatter as fm
import streamlit as st

st.set_page_config(
    page_title="Canvas Homes Link Engine",
    page_icon="🔗",
    layout="wide",
)

from link_engine.config import get_config
from link_engine.db.models import Anchor, Article, Error, Injection, Match, Run
from link_engine.reports.reporter import write_reports
from link_engine.stages.inject import inject_approved_links


def get_db():
    from link_engine.db.session import get_session_factory
    factory = get_session_factory()
    return factory()


def make_url(slug: str) -> str:
    return f"https://canvas-homes.com/blogs/{slug}"


def slugify(text: str) -> str:
    if not text:
        return ""
    text = text.lower().strip()
    text = re.sub(r"[^\w\s-]", "", text)
    text = re.sub(r"[\s_-]+", "-", text)
    return text.strip("-")


# ── Sidebar ───────────────────────────────────────────────────────────────────
st.sidebar.title("🔗 Canvas Homes Link Engine")
tab_name = st.sidebar.radio(
    "Navigate",
    ["Review Queue", "All Articles", "Inject Approved", "Injected Posts", "Errors", "Run History"],
    index=0,
)
st.sidebar.markdown("---")
st.sidebar.caption("Semantic internal linking — human approved before injection.")


# ── Review Queue ──────────────────────────────────────────────────────────────
if tab_name == "Review Queue":
    st.title("Review Queue")
    session = get_db()

    pending = (
        session.query(Anchor)
        .filter(Anchor.status == "pending_review")
        .join(Anchor.match)
        .order_by(Match.similarity_score.desc())
        .all()
    )
    approved_count = session.query(Anchor).filter(Anchor.status == "approved").count()
    rejected_count = session.query(Anchor).filter(Anchor.status == "rejected").count()

    c1, c2, c3 = st.columns(3)
    c1.metric("Pending review", len(pending))
    c2.metric("Approved", approved_count)
    c3.metric("Rejected", rejected_count)

    if not pending:
        st.success("No pending links. All done!")
        session.close()
        st.stop()

    st.markdown("---")

    col_a, col_r, _ = st.columns([1, 1, 5])
    if col_a.button("Approve all", type="primary"):
        for a in pending:
            a.status = "approved"
        session.commit()
        st.rerun()
    if col_r.button("Reject all"):
        for a in pending:
            a.status = "rejected"
        session.commit()
        st.rerun()

    score_min = st.slider("Min similarity score", 0.0, 1.0, 0.0, 0.05)
    filtered = [a for a in pending if a.match.similarity_score >= score_min]
    st.markdown(f"**{len(filtered)} links to review**")
    st.markdown("---")

    for anchor in filtered:
        match = anchor.match
        source = match.source_chunk
        target = match.target_chunk
        score = match.similarity_score
        confidence = anchor.llm_confidence or 0

        target_url = make_url(target.article.slug)
        target_section = slugify(target.heading or "")
        full_link = f"{target_url}#{target_section}" if target_section else target_url

        icon = "🟢" if score >= 0.80 else "🟡" if score >= 0.65 else "🔴"

        with st.expander(
            f"{icon} **{source.article.title}** → **{target.article.title}** "
            f"| Score: {score:.2f} | Confidence: {confidence}/5",
            expanded=False,
        ):
            st.info(f" Matched on title phrase: **\"{anchor.match.matched_title_phrase or '—'}\"**")
            left, right = st.columns(2)
            
            with left:
                st.markdown("**Source passage**")
                text = source.text
                phrase = anchor.anchor_text or ""
                if phrase and phrase in text:
                    highlighted = text.replace(phrase, f"**`{phrase}`**", 1)
                else:
                    highlighted = text
                st.markdown(highlighted)

            with right:
                st.markdown(f"**Target section:** `{target.heading or 'Introduction'}`")
                st.markdown(f"**Target URL:** `{full_link}`")
                st.markdown("---")
                st.markdown(target.text)

            st.markdown("---")
            st.markdown(f"*LLM reasoning: {anchor.reasoning or 'N/A'}*")

            c1, c2, c3, c4 = st.columns([3, 1, 1, 1])
            new_text = c1.text_input(
                "Anchor text",
                value=anchor.edited_anchor or anchor.anchor_text or "",
                key=f"edit_{anchor.anchor_id}",
                label_visibility="collapsed",
            )
            if c2.button("Approve", key=f"app_{anchor.anchor_id}", type="primary"):
                anchor.status = "approved"
                if new_text and new_text != anchor.anchor_text:
                    anchor.edited_anchor = new_text
                session.commit()
                st.rerun()
            if c3.button("Reject", key=f"rej_{anchor.anchor_id}"):
                anchor.status = "rejected"
                session.commit()
                st.rerun()
            if c4.button("Save edit", key=f"sav_{anchor.anchor_id}"):
                anchor.edited_anchor = new_text
                anchor.status = "approved"
                session.commit()
                st.rerun()

    session.close()


# ── All Articles ──────────────────────────────────────────────────────────────
elif tab_name == "All Articles":
    st.title("All Articles")
    session = get_db()

    articles = session.query(Article).order_by(Article.title).all()

    if not articles:
        st.info("No articles ingested yet. Run: `python -m link_engine.cli run ./test_posts`")
        session.close()
        st.stop()

    st.metric("Total articles", len(articles))
    st.markdown("---")

    search = st.text_input("Search articles", placeholder="Filter by title or slug...")

    filtered = [
        a for a in articles
        if not search or search.lower() in a.title.lower() or search.lower() in a.slug.lower()
    ]

    for article in filtered:
        chunk_count = len(article.chunks)
        injected_count = sum(
            1 for chunk in article.chunks
            for match in chunk.source_matches
            if match.anchor and match.anchor.injection and match.anchor.injection.status == "injected"
        )

        with st.expander(
            f"**{article.title}**  |  {chunk_count} chunks  |  {injected_count} links injected",
            expanded=False,
        ):
            # Metadata row
            col1, col2 = st.columns(2)
            col1.markdown(f"**Slug:** `{article.slug}`")
            col1.markdown(f"**URL:** [{make_url(article.slug)}]({make_url(article.slug)})")
            col2.markdown(f"**Status:** `{article.status}`")
            col2.markdown(f"**File:** `{Path(article.file_path).name}`")

            st.markdown("---")

            # Chunk list
            st.markdown("**Sections (chunks):**")
            for chunk in sorted(article.chunks, key=lambda c: c.position_index or 0):
                st.markdown(
                    f"- `{chunk.heading or 'Introduction'}` — "
                    f"{chunk.word_count} words — "
                    f"`{make_url(article.slug)}#{slugify(chunk.heading or '')}`"
                )

            st.markdown("---")

            # Full article content
            st.markdown("**Full article content:**")
            file_path = Path(article.file_path)
            if file_path.exists():
                raw = file_path.read_text(encoding="utf-8")
                post = fm.loads(raw)
                st.markdown(post.content)
            else:
                st.warning(f"File not found: {file_path}")

    session.close()


# ── Inject Approved ───────────────────────────────────────────────────────────
elif tab_name == "Inject Approved":
    st.title("Inject Approved Links")
    session = get_db()

    approved = (
        session.query(Anchor)
        .filter(Anchor.status == "approved")
        .filter(
            ~Anchor.anchor_id.in_(session.query(Injection.anchor_id))
        )
        .all()
    )

    st.metric("Approved links ready to inject", len(approved))

    if not approved:
        st.info("No approved links pending injection. Go to Review Queue first.")
        session.close()
        st.stop()

    st.markdown("**Links to be injected:**")
    for anchor in approved:
        phrase = anchor.edited_anchor or anchor.anchor_text
        src_title = anchor.match.source_chunk.article.title
        tgt_title = anchor.match.target_chunk.article.title
        tgt_slug = anchor.match.target_chunk.article.slug
        tgt_heading = anchor.match.target_chunk.heading or ""
        tgt_section = slugify(tgt_heading)
        tgt_url = make_url(tgt_slug)
        full_url = f"{tgt_url}#{tgt_section}" if tgt_section else tgt_url

        st.markdown(
            f"- `{phrase}` — **{src_title}** → **{tgt_title}**  \n"
            f"  Link: `[{phrase}]({full_url})`"
        )

    st.markdown("---")
    dry_run = st.checkbox("Dry run (preview only — do not modify files)", value=True)

    if st.button("Inject links", type="primary"):
        run = Run(articles_processed=0)
        session.add(run)
        session.flush()

        with st.spinner("Injecting..."):
            results = inject_approved_links(approved, session, run.run_id, dry_run=dry_run)
            session.commit()

        st.success(
            f"Done!  Injected: {results['injected']}  |  "
            f"Errors: {results['errors']}  |  Skipped: {results['skipped']}"
        )
        if not dry_run:
            write_reports(run.run_id, session)
            st.info("Reports written to ./output/")

    session.close()


# ── Injected Posts ────────────────────────────────────────────────────────────
elif tab_name == "Injected Posts":
    st.title("Injected Posts")
    session = get_db()

    injections = (
        session.query(Injection)
        .filter_by(status="injected")
        .order_by(Injection.injected_at.desc())
        .all()
    )

    if not injections:
        st.info("No injected links yet. Go to Inject Approved first.")
        session.close()
        st.stop()

    # Group by source article
    by_article: dict = {}
    for inj in injections:
        anchor = inj.anchor
        article = anchor.match.source_chunk.article
        aid = article.article_id
        if aid not in by_article:
            by_article[aid] = {"article": article, "injections": []}
        by_article[aid]["injections"].append(inj)

    c1, c2 = st.columns(2)
    c1.metric("Modified articles", len(by_article))
    c2.metric("Total links injected", len(injections))
    st.markdown("---")

    for aid, data in by_article.items():
        article = data["article"]
        article_injections = data["injections"]
        article_url = make_url(article.slug)

        with st.expander(
            f"**{article.title}**  —  {len(article_injections)} link(s) injected",
            expanded=True,
        ):
            # Metadata
            st.markdown(f"**URL:** [{article_url}]({article_url})")
            st.markdown("---")

            # Link summary table
            st.markdown("**Injected links:**")
            for inj in article_injections:
                anchor = inj.anchor
                match = anchor.match
                phrase = anchor.edited_anchor or anchor.anchor_text
                tgt_title = match.target_chunk.article.title
                tgt_slug = match.target_chunk.article.slug
                tgt_heading = match.target_chunk.heading or ""
                tgt_section = slugify(tgt_heading)
                tgt_url = make_url(tgt_slug)
                full_url = f"{tgt_url}#{tgt_section}" if tgt_section else tgt_url
                injected_at = inj.injected_at.strftime("%Y-%m-%d %H:%M") if inj.injected_at else "—"

                c1, c2, c3 = st.columns([3, 4, 2])
                c1.markdown(f"`{phrase}`")
                c2.markdown(f"[{full_url}]({full_url})")
                c3.caption(injected_at)

            st.markdown("---")

            # Full article with view toggle
            file_path = Path(article.file_path)
            if not file_path.exists():
                st.error(f"File not found: {file_path}")
            else:
                raw = file_path.read_text(encoding="utf-8")

                view = st.radio(
                    "View",
                    ["Rendered (with live links)", "Raw markdown"],
                    key=f"view_{aid}",
                    horizontal=True,
                )

                if view == "Raw markdown":
                    # Mark injected links with >>> <
                    display = raw
                    for inj in article_injections:
                        anchor = inj.anchor
                        phrase = anchor.edited_anchor or anchor.anchor_text
                        tgt_slug = anchor.match.target_chunk.article.slug
                        tgt_heading = anchor.match.target_chunk.heading or ""
                        tgt_section = slugify(tgt_heading)
                        tgt_url = make_url(tgt_slug)
                        full_url = f"{tgt_url}#{tgt_section}" if tgt_section else tgt_url
                        link_md = f"[{phrase}]({full_url})"
                        display = display.replace(link_md, f">>> {link_md} <<<")
                    st.code(display, language="markdown")

                else:
                    post = fm.loads(raw)
                    meta = dict(post.metadata)
                    if meta:
                        tags = meta.get("tags", [])
                        tags_str = ", ".join(tags) if isinstance(tags, list) else str(tags)
                        st.caption(
                            f"Title: {meta.get('title', '—')}  |  "
                            f"URL: {article_url}  |  "
                            f"Tags: {tags_str}"
                        )
                    # Render full content — markdown links render as clickable
                    st.markdown(post.content, unsafe_allow_html=False)

            st.markdown("---")

            # Restore button
            backup_path = article_injections[0].backup_path
            if backup_path and Path(backup_path).exists():
                st.caption(f"Backup: `{backup_path}`")
                if st.button("Restore original (undo)", key=f"restore_{aid}"):
                    shutil.copy2(backup_path, file_path)
                    for inj in article_injections:
                        inj.status = "skipped"
                        inj.error_message = "Manually restored from backup"
                    session.commit()
                    st.success(f"Restored {article.title}.")
                    st.rerun()
            else:
                st.caption("No backup found.")

    session.close()


# ── Errors ────────────────────────────────────────────────────────────────────
elif tab_name == "Errors":
    st.title("Error Dashboard")
    session = get_db()

    errors = session.query(Error).filter(Error.resolved_at.is_(None)).all()

    if not errors:
        st.success("No unresolved errors.")
        session.close()
        st.stop()

    st.metric("Unresolved errors", len(errors))
    st.markdown("---")

    for err in errors:
        with st.expander(
            f"[{err.stage.upper()}] {err.error_type} — {err.message[:80]}",
            expanded=False,
        ):
            st.markdown(f"**Stage:** `{err.stage}`")
            st.markdown(f"**Type:** `{err.error_type}`")
            st.markdown(f"**Message:** {err.message}")
            if err.article_id:
                st.markdown(f"**Article:** `{err.article_id}`")
            st.caption(f"Error ID: {err.error_id} | {err.created_at}")
            if err.rerun_eligible:
                if st.button("Rerun", key=f"rerun_{err.error_id}"):
                    err.resolved_at = datetime.utcnow()
                    session.commit()
                    st.success(f"Queued for rerun: `link-engine rerun --error-id {err.error_id}`")

    session.close()


# ── Run History ───────────────────────────────────────────────────────────────
elif tab_name == "Run History":
    st.title("Run History")
    session = get_db()

    runs = session.query(Run).order_by(Run.started_at.desc()).limit(20).all()

    if not runs:
        st.info("No runs yet.")
        session.close()
        st.stop()

    for run in runs:
        duration = "In progress"
        if run.completed_at and run.started_at:
            secs = (run.completed_at - run.started_at).total_seconds()
            duration = f"{secs:.1f}s"

        with st.expander(
            f"Run {run.run_id[:8]} | {run.started_at.strftime('%Y-%m-%d %H:%M')} | {duration}",
            expanded=False,
        ):
            c1, c2, c3, c4 = st.columns(4)
            c1.metric("Articles", run.articles_processed or 0)
            c2.metric("Injected", run.links_injected or 0)
            c3.metric("Matches", run.matches_found or 0)
            c4.metric("Errors", run.errors_total or 0)
            st.caption(f"Run ID: {run.run_id}")

    session.close()