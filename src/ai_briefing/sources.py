from __future__ import annotations

import calendar
import re
from datetime import datetime, timedelta, timezone
from urllib.parse import urlsplit, urlunsplit

import feedparser

from .config import Feed
from .models import NewsItem

_HTML_RE = re.compile(r"<[^>]+>")
_WS_RE = re.compile(r"\s+")


def _clean(value: str, limit: int = 700) -> str:
    return _WS_RE.sub(" ", _HTML_RE.sub(" ", value or "")).strip()[:limit]


def _entry_time(entry: object) -> datetime | None:
    for field in ("published_parsed", "updated_parsed"):
        parsed = entry.get(field)  # type: ignore[attr-defined]
        if parsed:
            try:
                return datetime.fromtimestamp(calendar.timegm(parsed), tz=timezone.utc)
            except (OverflowError, OSError, ValueError):
                pass
    return None


def canonical_url(url: str) -> str:
    """Remove fragments/query strings solely for de-duplication."""
    parts = urlsplit(url)
    return urlunsplit((parts.scheme.lower(), parts.netloc.lower(), parts.path.rstrip("/"), "", ""))


def collect(feeds: list[Feed], lookback_hours: int, max_per_feed: int, candidate_limit: int) -> list[NewsItem]:
    since = datetime.now(timezone.utc) - timedelta(hours=lookback_hours)
    seen: set[str] = set()
    collected: list[NewsItem] = []
    for feed in feeds:
        parsed = feedparser.parse(feed.url)
        if parsed.bozo and not parsed.entries:
            print(f"[warn] Feed unavailable: {feed.name}")
            continue
        accepted = 0
        for entry in parsed.entries:
            published_at = _entry_time(entry)
            title = _clean(entry.get("title", ""), 300)
            url = str(entry.get("link", "")).strip()
            if not published_at or published_at < since or not title or not url:
                continue
            key = canonical_url(url)
            if key in seen:
                continue
            seen.add(key)
            collected.append(NewsItem(
                source=feed.name, title=title, url=url, published_at=published_at,
                excerpt=_clean(entry.get("summary", entry.get("description", ""))),
            ))
            accepted += 1
            if accepted >= max_per_feed:
                break
    return sorted(collected, key=lambda item: item.published_at, reverse=True)[:candidate_limit]
