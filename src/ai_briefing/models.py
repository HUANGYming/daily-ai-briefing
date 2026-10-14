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


@dataclass(frozen=True)
class BriefItem:
    source: str
    title: str
    url: str
    published_at: datetime
    headline: str
    summary: str
    business_relevance: str
    category: str
    score: int

