import sys, json
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from link_engine.db.session import get_session
from link_engine.db.models import Article

with get_session() as s:
    for a in s.query(Article).order_by(Article.title).all():
        phrases = json.loads(a.title_phrases_json or "[]")
        print(f"\n{a.title!r}")
        print(f"  slug: {a.slug}")
        if phrases:
            for p in phrases:
                print(f"    - {p!r}")
        else:
            print("    (NO PHRASES DERIVED)")