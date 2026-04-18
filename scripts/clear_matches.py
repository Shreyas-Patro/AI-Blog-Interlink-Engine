import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from link_engine.db.session import get_session
from link_engine.db.models import Match, Anchor, Injection

with get_session() as s:
    s.query(Injection).delete()
    s.query(Anchor).delete()
    s.query(Match).delete()
print("cleared matches, anchors, injections")