import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from collections import Counter
from link_engine.db.session import get_session
from link_engine.db.models import Article, Chunk


def ngrams(text: str, n: int):
    # crude word tokeniser
    words = [w.strip(".,;:!?()[]\"'").lower() for w in text.split()]
    words = [w for w in words if w]
    for i in range(len(words) - n + 1):
        yield " ".join(words[i:i + n])


with get_session() as s:
    articles = s.query(Article).all()
    # For each article, collect the set of all 3-grams and 4-grams in its body text
    article_ngrams = {}
    for a in articles:
        text = "\n".join(c.text for c in a.chunks)
        grams = set()
        for n in (3, 4, 5):
            for g in ngrams(text, n):
                grams.add(g)
        article_ngrams[a.article_id] = (a.title, grams)

    # Count ngrams that appear in at least 2 articles
    gram_appearances = Counter()
    for _title, grams in article_ngrams.values():
        for g in grams:
            gram_appearances[g] += 1

    shared = [(g, c) for g, c in gram_appearances.items() if c >= 2]
    shared.sort(key=lambda x: (-x[1], -len(x[0].split())))

    print(f"Phrases appearing in 2+ articles (top 60 longest/most common):\n")
    printed = 0
    seen_ok = 0
    for phrase, count in shared:
        words = phrase.split()
        # Skip super-generic short ones for readability
        if len(words) < 3:
            continue
        # Skip phrases that are mostly stopwords
        stops = {"the", "a", "an", "and", "or", "of", "to", "in", "on", "is", "are", "for", "with", "you", "it", "this", "that", "as", "by", "be", "have"}
        content_words = [w for w in words if w not in stops]
        if len(content_words) < 2:
            continue
        print(f"  [{count} articles] {phrase!r}")
        printed += 1
        if printed >= 60:
            break