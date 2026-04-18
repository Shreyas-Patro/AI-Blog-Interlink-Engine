import sys, json
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from link_engine.db.session import get_session
from link_engine.db.models import Article, Chunk

with get_session() as s:
    articles = s.query(Article).all()
    chunks = s.query(Chunk).all()
    print(f"{len(articles)} articles, {len(chunks)} chunks\n")

    hits = 0
    for target in articles:
        phrases = json.loads(target.title_phrases_json or "[]")
        for phrase in phrases:
            for chunk in chunks:
                if chunk.article_id == target.article_id:
                    continue
                if phrase.lower() in chunk.text.lower():
                    src_title = next(a.title for a in articles if a.article_id == chunk.article_id)
                    print(f"HIT: '{phrase}'")
                    print(f"  from: {src_title!r}")
                    print(f"  to:   {target.title!r}")
                    hits += 1
                    break
    print(f"\n{hits} lexical hits found")