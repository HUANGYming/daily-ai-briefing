from datetime import datetime, timezone

from ai_briefing.config import SearchConfig
from ai_briefing import search


def test_tavily_results_become_news_items(monkeypatch):
    monkeypatch.setenv("TAVILY_API_KEY", "test-key")
    monkeypatch.setattr(search, "_tavily_request", lambda *_: [{
        "title": "New AI release",
        "url": "https://example.test/news",
        "content": "A public result snippet.",
        "published_date": "Tue, 14 Oct 2026 10:00:00 GMT",
    }])
    config = SearchConfig(enabled=True, queries=["AI releases"])
    items = search.collect(config)
    assert items[0].source == "Tavily · example.test"
    assert items[0].published_at == datetime(2026, 10, 14, 10, tzinfo=timezone.utc)
