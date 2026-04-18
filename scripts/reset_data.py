import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from link_engine.db.session import get_session
from link_engine.db.models import (
    Injection, Anchor, Match, Embedding, Chunk, Article, Error, Run
)

with get_session() as s:
    # Delete in FK-dependency order: children first
    s.query(Injection).delete()
    s.query(Anchor).delete()
    s.query(Match).delete()
    s.query(Embedding).delete()
    s.query(Chunk).delete()
    s.query(Error).delete()
    s.query(Run).delete()
    s.query(Article).delete()
print("cleared all data. schema intact.")