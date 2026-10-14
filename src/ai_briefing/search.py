"""External search providers used only to discover public-news candidates."""
from __future__ import annotations

import json
import os
import urllib.error
import urllib.request
from datetime import datetime, timezone
from email.utils import parsedate_to_datetime
from typing import Any
from urllib.parse import urlsplit

from .config import SearchConfig
from .models import NewsItem

TAVILY_SEARCH_URL = "https://api.tavily.com/search"


def _published_at(value: object) -> datetime:
    if isinstance(value, str) and value:
        try:
            parsed = parsedate_to_datetime(value)
            return parsed if parsed.tzinfo else parsed.replace(tzinfo=timezone.utc)
        except (TypeError, ValueError, IndexError):
            pass
        try:
            parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
            return parsed if parsed.tzinfo else parsed.replace(tzinfo=timezone.utc)
        except ValueError:
            pass
    return datetime.now(timezone.utc)


def _source_name(url: str) -> str:
    return f"Tavily · {urlsplit(url).netloc or 'Web'}"


def _tavily_request(query: str, config: SearchConfig, api_key: str) -> list[dict[str, Any]]:
    payload = json.dumps({
        "query": query,
        "topic": "news",
        "search_depth": config.search_depth,
        "max_results": config.max_results_per_query,
        "time_range": config.time_range,
        "filter_by_published_date": True,
        "include_answer": False,
        "include_raw_content": False,
        "include_usage": False,
        "safe_search": True,
    }).encode("utf-8")
    request = urllib.request.Request(
        TAVILY_SEARCH_URL,
        data=payload,
        headers={"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"},
        method="POST",
    )
    with urllib.request.urlopen(request, timeout=25) as response:
        decoded = json.load(response)
    results = decoded.get("results", [])
    return results if isinstance(results, list) else []


def collect(config: SearchConfig) -> list[NewsItem]:
    """Fetch a bounded set of Tavily news candidates; outages don't block RSS."""
    if not config.enabled:
        return []
    api_key = os.environ.get("TAVILY_API_KEY")
    if not api_key:
        raise RuntimeError("已启用 Tavily 搜索，但未设置 TAVILY_API_KEY")
    items: list[NewsItem] = []
    for query in config.queries or []:
        try:
            results = _tavily_request(query, config, api_key)
        except (urllib.error.HTTPError, urllib.error.URLError, TimeoutError, json.JSONDecodeError) as exc:
            print(f"[warn] Tavily search failed for {query!r}: {exc}")
            continue
        for result in results:
            if not isinstance(result, dict):
                continue
            title = str(result.get("title", "")).strip()
            url = str(result.get("url", "")).strip()
            if not title or not url:
                continue
            items.append(NewsItem(
                source=_source_name(url),
                title=title,
                url=url,
                published_at=_published_at(result.get("published_date")),
                excerpt=str(result.get("content", "")).strip()[:700],
            ))
    return items
