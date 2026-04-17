#!/usr/bin/env python3
import json
import subprocess
import sys
import uuid
from datetime import datetime
from pathlib import Path
from typing import Optional

import typer
from rich.console import Console
from rich.progress import track
from rich.table import Table

app = typer.Typer(help="AI-powered internal link engine")
console = Console()


def _get_session_and_run():
    from link_engine.db.session import get_session_factory
    from link_engine.db.models import Run
    from link_engine.config import get_config
    import json

    factory = get_session_factory()
    session = factory()
    cfg = get_config()
    run = Run(config_json=json.dumps(cfg))
    session.add(run)
    session.flush()
    return session, run


@app.command()
def run(
    content_dir: Path = typer.Argument(..., help="Directory of markdown files"),
    dry_run: bool = typer.Option(False, "--dry-run", help="Preview injections without writing"),
):
    """Run the full pipeline on a directory of markdown files."""
    from link_engine.stages.ingest import ingest_directory
    from link_engine.stages.chunk import chunk_all_articles
    from link_engine.stages.embed import embed_all_pending
    from link_engine.stages.match import compute_matches
    from link_engine.stages.anchor import generate_all_anchors
    from link_engine.db.models import Run

    if not content_dir.exists():
        console.print(f"[red]Directory not found: {content_dir}[/red]")
        raise typer.Exit(1)

    session, pipeline_run = _get_session_and_run()
    run_id = pipeline_run.run_id
    console.print(f"\n[bold blue]🔗 Link Engine[/bold blue]  Run ID: {run_id[:8]}...\n")

    # Stage 1: Ingest
    console.print("[bold]Stage 1/5:[/bold] Ingesting articles...")
    results = ingest_directory(content_dir, run_id, session)
    session.commit()
    changed = results["new"] + results["changed"]
    console.print(
        f"  ✓ {len(results['new'])} new  |  {len(results['changed'])} changed  |  "
        f"{len(results['unchanged'])} unchanged  |  {results['errors']} errors"
    )
    pipeline_run.articles_processed = len(changed)

    if not changed:
        console.print("[yellow]No changed articles to process.[/yellow]")
        session.commit()
        session.close()
        return

    # Stage 2: Chunk
    console.print("[bold]Stage 2/5:[/bold] Chunking articles...")
    total_chunks = chunk_all_articles(changed, session)
    session.commit()
    console.print(f"  ✓ {total_chunks} chunks created")
    pipeline_run.chunks_created = total_chunks

    # Stage 3: Embed
    console.print("[bold]Stage 3/5:[/bold] Computing embeddings (cached)...")
    n_computed = embed_all_pending(session)
    session.commit()
    console.print(f"  ✓ {n_computed} new embeddings computed")
    pipeline_run.embeddings_computed = n_computed

    # Stage 4: Match
    console.print("[bold]Stage 4/5:[/bold] Computing semantic matches...")
    n_matches = compute_matches(session, run_id)
    session.commit()
    console.print(f"  ✓ {n_matches} new matches found")
    pipeline_run.matches_found = n_matches

    # Stage 5: Anchors
    console.print("[bold]Stage 5/5:[/bold] Generating anchor text (LLM)...")
    anchor_results = generate_all_anchors(session, run_id)
    session.commit()
    console.print(
        f"  ✓ {anchor_results['success']} anchors generated  |  "
        f"{anchor_results.get('cached', 0)} from cache  |  "
        f"{anchor_results['errors']} errors"
    )

    pipeline_run.completed_at = datetime.utcnow()
    session.commit()

    console.print(
        f"\n[bold green]✓ Pipeline complete![/bold green]\n"
        f"  Run the dashboard to review and approve links:\n"
        f"  [cyan]python -m link_engine.cli dashboard[/cyan]\n"
    )
    session.close()


@app.command()
def dashboard():
    """Launch the HITL review dashboard."""
    console.print("[bold blue]Launching dashboard...[/bold blue]")
    subprocess.run([
        sys.executable, "-m", "streamlit", "run",
        "link_engine/dashboard/app.py",
        "--server.headless", "true",
    ])


@app.command()
def status():
    """Show current pipeline status."""
    from link_engine.db.session import get_session_factory
    from link_engine.db.models import Anchor, Match, Error, Article

    factory = get_session_factory()
    session = factory()

    table = Table(title="Pipeline Status")
    table.add_column("Metric", style="bold")
    table.add_column("Count", justify="right")

    table.add_row("Total articles", str(session.query(Article).count()))
    table.add_row("Pending anchor review", str(session.query(Anchor).filter_by(status="pending_review").count()))
    table.add_row("Approved links", str(session.query(Anchor).filter_by(status="approved").count()))
    table.add_row("Rejected links", str(session.query(Anchor).filter_by(status="rejected").count()))
    table.add_row("Anchor errors", str(session.query(Match).filter_by(status="anchor_error").count()))
    table.add_row("Unresolved errors", str(session.query(Error).filter(Error.resolved_at.is_(None)).count()))

    console.print(table)
    session.close()


@app.command()
def rerun(
    error_id: Optional[str] = typer.Option(None, "--error-id"),
    stage: Optional[str] = typer.Option(None, "--stage"),
    all_errors: bool = typer.Option(False, "--all-errors"),
):
    """Re-queue failed items for reprocessing."""
    from link_engine.db.session import get_session_factory
    from link_engine.db.models import Error, Match, Chunk
    from link_engine.stages.anchor import generate_anchor
    from link_engine.stages.embed import embed_chunks

    factory = get_session_factory()
    session = factory()

    query = session.query(Error).filter(Error.resolved_at.is_(None), Error.rerun_eligible == True)

    if error_id:
        query = query.filter(Error.error_id == error_id)
    elif stage:
        query = query.filter(Error.stage == stage)
    elif not all_errors:
        console.print("[red]Specify --error-id, --stage, or --all-errors[/red]")
        raise typer.Exit(1)

    errors = query.all()
    if not errors:
        console.print("[yellow]No eligible errors found.[/yellow]")
        return

    console.print(f"Rerunning {len(errors)} error(s)...")

    for err in errors:
        try:
            if err.stage == "anchor" and err.match_id:
                match = session.get(Match, err.match_id)
                if match:
                    match.status = "pending_anchor"
                    session.flush()
                    success = generate_anchor(match, session)
                    if success:
                        err.resolved_at = datetime.utcnow()
                        console.print(f"  ✓ Anchor rerun success: {err.error_id[:8]}")
                    else:
                        console.print(f"  ✗ Anchor rerun failed: {err.error_id[:8]}")

            elif err.stage == "embedding" and err.chunk_id:
                chunk = session.get(Chunk, err.chunk_id)
                if chunk:
                    embed_chunks([chunk], session)
                    err.resolved_at = datetime.utcnow()
                    console.print(f"  ✓ Embedding rerun success: {err.error_id[:8]}")

            else:
                console.print(f"  → Manual rerun needed for stage '{err.stage}': {err.error_id[:8]}")

            session.commit()

        except Exception as e:
            session.rollback()
            console.print(f"  ✗ Rerun failed: {e}")

    session.close()

@app.command()
def debug_scores():
    """Print actual similarity scores between chunks to tune threshold."""
    from link_engine.db.session import get_session_factory
    from link_engine.db.models import Chunk, Embedding
    from link_engine.stages.embed import bytes_to_vector
    import numpy as np

    factory = get_session_factory()
    session = factory()

    embeddings = session.query(Embedding).all()
    if len(embeddings) < 2:
        console.print("[red]Not enough embeddings. Run the pipeline first.[/red]")
        return

    chunk_ids = []
    vectors = []
    chunk_to_article = {}
    chunk_to_heading = {}

    for emb in embeddings:
        chunk = session.get(Chunk, emb.chunk_id)
        if chunk is None:
            continue
        vec = bytes_to_vector(emb.vector)
        chunk_ids.append(emb.chunk_id)
        vectors.append(vec)
        chunk_to_article[emb.chunk_id] = chunk.article.title[:30]
        chunk_to_heading[emb.chunk_id] = (chunk.heading or "intro")[:25]

    matrix = np.vstack(vectors).astype(np.float32)
    norms = np.linalg.norm(matrix, axis=1, keepdims=True)
    normalized = matrix / norms
    sim = normalized @ normalized.T

    n = len(chunk_ids)

    # Collect all cross-article pairs
    pairs = []
    for i in range(n):
        for j in range(i + 1, n):
            if chunk_to_article[chunk_ids[i]] != chunk_to_article[chunk_ids[j]]:
                pairs.append((float(sim[i][j]), chunk_ids[i], chunk_ids[j]))

    pairs.sort(reverse=True)

    console.print("\n[bold]Top 15 cross-article similarity scores:[/bold]")
    console.print(f"{'Score':>6}  {'Source':30}  {'Target':30}")
    console.print("-" * 75)
    for score, sid, tid in pairs[:15]:
        src = f"{chunk_to_article[sid]}: {chunk_to_heading[sid]}"
        tgt = f"{chunk_to_article[tid]}: {chunk_to_heading[tid]}"
        color = "green" if score >= 0.75 else "yellow" if score >= 0.50 else "red"
        console.print(f"[{color}]{score:>6.3f}[/{color}]  {src:30}  {tgt:30}")

    console.print("\n[dim]Green = above 0.75  Yellow = 0.50-0.75  Red = below 0.50[/dim]")
    session.close()
    

@app.command()
def rerun(
    error_id: Optional[str] = typer.Option(None, "--error-id"),
    stage: Optional[str] = typer.Option(None, "--stage"),
    all_errors: bool = typer.Option(False, "--all-errors"),
):
    """Re-queue failed items for reprocessing."""
    from link_engine.db.session import get_session_factory
    from link_engine.db.models import Error, Match, Chunk
    from link_engine.stages.anchor import generate_anchor
    from link_engine.stages.embed import embed_chunks

    factory = get_session_factory()
    session = factory()

    query = session.query(Error).filter(
        Error.resolved_at.is_(None),
        Error.rerun_eligible == True,
    )

    if error_id:
        query = query.filter(Error.error_id == error_id)
    elif stage:
        query = query.filter(Error.stage == stage)
    elif not all_errors:
        console.print("[red]Specify --error-id, --stage, or --all-errors[/red]")
        raise typer.Exit(1)

    errors = query.all()
    if not errors:
        console.print("[yellow]No eligible errors found.[/yellow]")
        return

    console.print(f"Rerunning {len(errors)} error(s)...")

    for err in errors:
        try:
            if err.stage == "anchor" and err.match_id:
                match = session.get(Match, err.match_id)
                if match:
                    match.status = "pending_anchor"
                    session.flush()
                    success = generate_anchor(match, session)
                    if success:
                        err.resolved_at = datetime.utcnow()
                        console.print(f"  Anchor rerun success: {err.error_id[:8]}")
                    else:
                        console.print(f"  Anchor rerun failed: {err.error_id[:8]}")

            elif err.stage == "embedding" and err.chunk_id:
                chunk = session.get(Chunk, err.chunk_id)
                if chunk:
                    embed_chunks([chunk], session)
                    err.resolved_at = datetime.utcnow()
                    console.print(f"  Embedding rerun success: {err.error_id[:8]}")

            else:
                console.print(f"  Manual rerun needed for stage '{err.stage}': {err.error_id[:8]}")

            session.commit()

        except Exception as e:
            session.rollback()
            console.print(f"  Rerun failed: {e}")

    session.close()

if __name__ == "__main__":
    app()