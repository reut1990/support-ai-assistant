"""Finds the help articles most likely to answer a ticket, before anything is sent to the AI.

This is the "search" half of answering from a knowledge base: only the best few articles go to the AI,
which keeps each call small and cheap and makes the AI's sources easy to check. It uses BM25, a classic
keyword-ranking formula used by search engines, so it runs locally for free.
"""

import math
import re
from collections import Counter

from src.models import Article

STOPWORDS = set("""a an and are as at be but by can do does for from has have how i if in into is it its
my me no not of on or our so that the their them then there this to was we were what when where which
who why will with you your yes hi hello thanks thank please just get got any all also im ive dont""".split())


def tokens(text: str) -> list[str]:
    words = re.findall(r"[a-z0-9]+", text.lower())
    return [_stem(w) for w in words if w not in STOPWORDS and len(w) > 1]


def _stem(word: str) -> str:
    # A very small stemmer, so "payouts" matches "payout" and "charged" matches "charge".
    for suffix in ("ing", "ed", "es", "s"):
        if word.endswith(suffix) and len(word) - len(suffix) >= 4:
            return word[: -len(suffix)]
    return word


class ArticleSearch:
    def __init__(self, articles: list[Article], k1: float = 1.5, b: float = 0.75):
        self.articles = articles
        self.k1, self.b = k1, b
        # The title counts three times, because it says what the article is mainly about.
        self.docs = [Counter(tokens(f"{a.title} {a.title} {a.title} {a.body}")) for a in articles]
        self.lengths = [sum(d.values()) for d in self.docs]
        self.avg_length = sum(self.lengths) / max(len(self.docs), 1)
        df = Counter(word for d in self.docs for word in d)
        n = len(self.docs)
        self.idf = {w: math.log(1 + (n - c + 0.5) / (c + 0.5)) for w, c in df.items()}

    def search(self, text: str, top: int = 3) -> list[Article]:
        query = set(tokens(text))
        scores = []
        for i, doc in enumerate(self.docs):
            score = 0.0
            for w in query:
                tf = doc.get(w, 0)
                if tf:
                    norm = tf * (self.k1 + 1) / (tf + self.k1 * (1 - self.b + self.b * self.lengths[i] / self.avg_length))
                    score += self.idf[w] * norm
            scores.append((score, i))
        scores.sort(reverse=True)
        return [self.articles[i] for score, i in scores[:top] if score > 0]
