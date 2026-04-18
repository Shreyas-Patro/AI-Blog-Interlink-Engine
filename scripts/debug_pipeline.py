import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from link_engine.db.session import get_session
from link_engine.db.models import Match, Anchor, Error, Injection

with get_session() as s:
    matches = s.query(Match).all()
    anchors = s.query(Anchor).all()
    injections = s.query(Injection).all()
    errors = s.query(Error).all()

    print(f"=== MATCHES: {len(matches)} total ===")
    for m in matches:
        src = m.source_chunk.article.title if m.source_chunk else "?"
        tgt = m.target_chunk.article.title if m.target_chunk else "?"
        print(f"  [{m.status}] {src!r} -> {tgt!r}")
        print(f"      phrase: {m.matched_phrase!r}  sim: {m.similarity_score:.3f}")

    print(f"\n=== ANCHORS: {len(anchors)} total ===")
    for a in anchors:
        print(f"  [{a.status}] conf={a.llm_confidence} anchor={a.anchor_text!r}")
        print(f"      reasoning: {(a.reasoning or '')[:100]}")

    print(f"\n=== INJECTIONS: {len(injections)} total ===")
    for i in injections:
        print(f"  [{i.status}] {i.error_message or ''}")

    print(f"\n=== ERRORS: {len(errors)} total ===")
    for e in errors:
        print(f"  [{e.stage}] {e.error_type}: {e.message[:120]}")
        