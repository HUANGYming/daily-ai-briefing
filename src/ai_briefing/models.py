from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime


@dataclass(frozen=True)
class NewsItem:
    source: str
    title: str
    url: str
    published_at: datetime
    excerpt: str = ""
    providers: frozenset[str] = frozenset()


@dataclass(frozen=True)
class BriefItem:
    source: str
    title: str
    url: str
    published_at: datetime
    headline: str
    summary: str
    category: str
    topic: str
    score: int
    rank_score: float = 0.0
