from datetime import datetime, timedelta, timezone

from ai_briefing.models import BriefItem, NewsItem
from ai_briefing.ranking import rank_and_deduplicate


NOW = datetime(2026, 10, 15, tzinfo=timezone.utc)


def _brief(url: str, topic: str, score: int) -> BriefItem:
    return BriefItem("source", "original", url, NOW, "Headline", "Summary", "model", topic, score)


def test_ranking_rewards_official_cross_provider_evidence():
    official = NewsItem("source", "title", "https://openai.com/news/model", NOW, providers=frozenset({"rss", "brave"}))
    unknown = NewsItem("source", "title", "https://example.test/model", NOW, providers=frozenset({"tavily"}))
    ranked = rank_and_deduplicate(
        [_brief(official.url, "official-model", 8), _brief(unknown.url, "unknown-model", 8)], [official, unknown], NOW
    )
    assert ranked[0].url == official.url
    assert ranked[0].rank_score > ranked[1].rank_score


def test_ranking_keeps_one_report_per_topic():
    first = NewsItem("source", "title", "https://example.test/first", NOW, providers=frozenset({"rss"}))
    second = NewsItem("source", "title", "https://example.test/second", NOW - timedelta(hours=12), providers=frozenset({"rss"}))
    ranked = rank_and_deduplicate(
        [_brief(first.url, "same-event", 9), _brief(second.url, "same-event", 8)], [first, second], NOW
    )
    assert [item.url for item in ranked] == [first.url]
