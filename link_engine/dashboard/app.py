import re
import shutil
from datetime import datetime
from pathlib import Path

import frontmatter as fm
import streamlit as st

st.set_page_config(
    page_title="Link Engine Dashboard",
    page_icon="🔗",
    layout="wide",
)

from link_engine.config import get_config
from link_engine.db.models import Anchor, Error, Injection, Match, Run
from link_engine.reports.reporter import write_reports
from link_engine.stages.inject import inject_approved_links


def get_db():
    from link_engine.db.session import get_session_factory
    factory = get_session_factory()
    return factory()


# ── Sidebar ───────────────────────────────────────────────────────────────────
st.sidebar.title("🔗 Link Engine")
tab_name = st.sidebar.radio(
    "Navigate",
    ["Review Queue", "Errors", "Run History", "Inject Approved", "Injected Posts"],
    index=0,
)
st.sidebar.markdown("---")
st.sidebar.caption("Approve links before injecting. Edit anchor text if needed.")


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
    approved = session.query(Anchor).filter(Anchor.status == "approved").count()
    rejected = session.query(Anchor).filter(Anchor.status == "rejected").count()

    col1, col2, col3 = st.columns(3)
    col1.metric("Pending", len(pending))
    col2.metric("Approved", approved)
    col3.metric("Rejected", rejected)

    if not pending:
        st.success("No pending links. All done!")
        session.close()
        st.stop()

    st.markdown("---")
    col_a, col_r, col_f = st.columns([1, 1, 4])
    if col_a.button("✅ Approve All", type="primary"):
        for anchor in pending:
            anchor.status = "approved"
        session.commit()
        st.rerun()

    if col_r.button("❌ Reject All"):
        for anchor in pending:
            anchor.status = "rejected"
        session.commit()
        st.rerun()

    score_filter = st.slider("Min similarity score", 0.0, 1.0, 0.0, 0.05)
    filtered = [a for a in pending if a.match.similarity_score >= score_filter]

    st.markdown(f"**Showing {len(filtered)} links**")
    st.markdown("---")

    for anchor in filtered:
        match = anchor.match
        source = match.source_chunk
        target = match.target_chunk
        score = match.similarity_score
        confidence = anchor.llm_confidence or 0

        with st.expander(
            f"{'🟢' if score >= 0.85 else '🟡' if score >= 0.75 else '🔴'} "
            f"**{source.article.title}** → **{target.article.title}**  |  "
            f"Score: {score:.2f}  |  Confidence: {confidence}/5",
            expanded=False,
        ):
            left, right = st.columns(2)

            with left:
                st.markdown("**Source passage:**")
                text = source.text
                phrase = anchor.anchor_text
                if phrase and phrase in text:
                    highlighted = text.replace(phrase, f"**`{phrase}`**", 1)
                else:
                    highlighted = text
                st.markdown(highlighted[:600] + ("..." if len(text) > 600 else ""))

            with right:
                st.markdown(f"**Target section:** `{target.heading or 'Introduction'}`")
                st.markdown(target.text[:400] + ("..." if len(target.text) > 400 else ""))

            st.markdown("---")
            c1, c2, c3, c4 = st.columns([2, 1, 1, 1])

            with c1:
                new_text = st.text_input(
                    "Anchor text",
                    value=anchor.edited_anchor or anchor.anchor_text or "",
                    key=f"edit_{anchor.anchor_id}",
                    label_visibility="collapsed",
                )
            with c2:
                if st.button("✅ Approve", key=f"approve_{anchor.anchor_id}"):
                    anchor.status = "approved"
                    if new_text and new_text != anchor.anchor_text:
                        anchor.edited_anchor = new_text
                    session.commit()
                    st.rerun()
            with c3:
                if st.button("❌ Reject", key=f"reject_{anchor.anchor_id}"):
                    anchor.status = "rejected"
                    session.commit()
                    st.rerun()
            with c4:
                if st.button("💾 Save Edit", key=f"save_{anchor.anchor_id}"):
                    anchor.edited_anchor = new_text
                    anchor.status = "approved"
                    session.commit()
                    st.rerun()

            st.caption(f"LLM reasoning: {anchor.reasoning or 'N/A'}")

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

    st.metric("Unresolved Errors", len(errors))

    if st.button("🔄 Rerun All Eligible Errors", type="primary"):
        st.info("Rerun triggered — check terminal for progress. Refresh after completion.")

    st.markdown("---")

    for err in errors:
        with st.expander(
            f"[{err.stage.upper()}] {err.error_type} — {err.message[:60]}...",
            expanded=False,
        ):
            st.markdown(f"**Stage:** `{err.stage}`")
            st.markdown(f"**Type:** `{err.error_type}`")
            st.markdown(f"**Message:** {err.message}")
            if err.article_id:
                st.markdown(f"**Article ID:** `{err.article_id}`")
            if err.chunk_id:
                st.markdown(f"**Chunk ID:** `{err.chunk_id}`")
            st.markdown(f"**Rerun eligible:** {'Yes' if err.rerun_eligible else 'No'}")
            st.caption(f"Error ID: {err.error_id} | Created: {err.created_at}")

            col_r, col_d = st.columns([1, 5])
            if err.rerun_eligible:
                if col_r.button("🔄 Rerun", key=f"rerun_{err.error_id}"):
                    err.resolved_at = datetime.utcnow()
                    session.commit()
                    st.success(f"Marked for rerun. Run CLI: `link-engine rerun --error-id {err.error_id}`")

    session.close()


# ── Run History ───────────────────────────────────────────────────────────────
elif tab_name == "Run History":
    st.title("Run History")
    session = get_db()

    runs = session.query(Run).order_by(Run.started_at.desc()).limit(20).all()

    if not runs:
        st.info("No runs yet. Run: `python -m link_engine.cli run ./test_posts`")
        session.close()
        st.stop()

    for run in runs:
        duration = "In progress..."
        if run.completed_at and run.started_at:
            secs = (run.completed_at - run.started_at).total_seconds()
            duration = f"{secs:.1f}s"

        with st.expander(
            f"Run {run.run_id[:8]}... | {run.started_at.strftime('%Y-%m-%d %H:%M')} | {duration}",
            expanded=False,
        ):
            col1, col2, col3, col4 = st.columns(4)
            col1.metric("Articles", run.articles_processed or 0)
            col2.metric("Links Injected", run.links_injected or 0)
            col3.metric("Matches Found", run.matches_found or 0)
            col4.metric("Errors", run.errors_total or 0)
            st.caption(f"Full Run ID: {run.run_id}")

    session.close()


# ── Inject Approved ───────────────────────────────────────────────────────────
elif tab_name == "Inject Approved":
    st.title("Inject Approved Links")
    session = get_db()

    approved = (
        session.query(Anchor)
        .filter(Anchor.status == "approved")
        .filter(~Anchor.anchor_id.in_(
            session.query(Injection.anchor_id)
        ))
        .all()
    )

    st.metric("Approved Links Ready to Inject", len(approved))

    if not approved:
        st.info("No approved links pending injection. Go to Review Queue to approve links first.")
        session.close()
        st.stop()

    st.markdown("**Links to be injected:**")
    for anchor in approved:
        phrase = anchor.edited_anchor or anchor.anchor_text
        src = anchor.match.source_chunk.article.title
        tgt = anchor.match.target_chunk.article.title
        st.markdown(f"- `{phrase}` — **{src}** → **{tgt}**")

    st.markdown("---")

    dry_run = st.checkbox("Dry run (preview only, don't modify files)", value=True)

    if st.button("🚀 Inject Links", type="primary"):
        run = Run(articles_processed=0)
        session.add(run)
        session.flush()

        with st.spinner("Injecting links..."):
            results = inject_approved_links(approved, session, run.run_id, dry_run=dry_run)
            session.commit()

        st.success(f"Done! Injected: {results['injected']} | Errors: {results['errors']} | Skipped: {results['skipped']}")

        if not dry_run:
            write_reports(run.run_id, session)
            st.info("Reports written to ./output/")

    session.close()


# ── Injected Posts Review ─────────────────────────────────────────────────────
elif tab_name == "Injected Posts":
    st.title("Injected Posts Review")
    session = get_db()

    injections = (
        session.query(Injection)
        .filter_by(status="injected")
        .order_by(Injection.injected_at.desc())
        .all()
    )

    if not injections:
        st.info("No injected links yet. Go to 'Inject Approved' tab first.")
        session.close()
        st.stop()

    # Group by source article
    by_article = {}
    for inj in injections:
        anchor = inj.anchor
        article = anchor.match.source_chunk.article
        aid = article.article_id
        if aid not in by_article:
            by_article[aid] = {"article": article, "injections": []}
        by_article[aid]["injections"].append(inj)

    col1, col2 = st.columns(2)
    col1.metric("Modified Articles", len(by_article))
    col2.metric("Total Links Injected", len(injections))
    st.markdown("---")

    for aid, data in by_article.items():
        article = data["article"]
        article_injections = data["injections"]

        with st.expander(
            f"📄 {article.title}  —  {len(article_injections)} link(s) injected",
            expanded=True,
        ):
            # Link summary
            st.markdown("**Injected links:**")
            for inj in article_injections:
                anchor = inj.anchor
                match = anchor.match
                phrase = anchor.edited_anchor or anchor.anchor_text
                target_title = match.target_chunk.article.title
                target_heading = match.target_chunk.heading or "Introduction"
                score = match.similarity_score
                confidence = anchor.llm_confidence or 0
                injected_at = inj.injected_at.strftime("%Y-%m-%d %H:%M") if inj.injected_at else "—"

                c1, c2, c3, c4, c5 = st.columns([3, 3, 1, 1, 2])
                c1.markdown(f"`{phrase}`")
                c2.markdown(f"→ **{target_title}** › *{target_heading}*")
                c3.markdown(f"`{score:.2f}`")
                c4.markdown(f"`{confidence}/5`")
                c5.caption(injected_at)

            st.markdown("---")

            # File preview
            file_path = Path(article.file_path)
            if not file_path.exists():
                st.error(f"File not found: {file_path}")
            else:
                raw = file_path.read_text(encoding="utf-8")

                view_mode = st.radio(
                    "View mode",
                    ["Rendered (with links)", "Raw markdown"],
                    key=f"view_{aid}",
                    horizontal=True,
                )

                if view_mode == "Raw markdown":
                    # Mark injected links with >>> <<< so they stand out
                    highlighted_raw = raw
                    for inj in article_injections:
                        anchor = inj.anchor
                        phrase = anchor.edited_anchor or anchor.anchor_text
                        target_url = anchor.match.target_chunk.article.url
                        heading = anchor.match.target_chunk.heading or ""
                        slug = re.sub(r'[^\w\s-]', '', heading.lower())
                        slug = re.sub(r'[\s_-]+', '-', slug).strip('-')
                        link_target = f"{target_url}#{slug}" if slug else target_url
                        link_md = f"[{phrase}]({link_target})"
                        highlighted_raw = highlighted_raw.replace(
                            link_md, f">>> {link_md} <<<"
                        )
                    st.code(highlighted_raw, language="markdown")

                else:
                    post = fm.loads(raw)
                    meta = dict(post.metadata)
                    if meta:
                        tags = meta.get("tags", [])
                        tags_str = ", ".join(tags) if isinstance(tags, list) else str(tags)
                        st.caption(
                            f"**Title:** {meta.get('title', '—')}  |  "
                            f"**URL:** {meta.get('url', '—')}  |  "
                            f"**Tags:** {tags_str}"
                        )
                    st.markdown(post.content)

            # Backup + restore
            st.markdown("---")
            backup_path = article_injections[0].backup_path
            if backup_path and Path(backup_path).exists():
                st.caption(f"💾 Backup: `{backup_path}`")
                if st.button("↩️ Restore original (undo all injections)", key=f"restore_{aid}"):
                    shutil.copy2(backup_path, file_path)
                    for inj in article_injections:
                        inj.status = "skipped"
                        inj.error_message = "Manually restored from backup"
                    session.commit()
                    st.success(f"Restored {article.title} from backup.")
                    st.rerun()
            else:
                st.caption("No backup found for this article.")

    session.close()