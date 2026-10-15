"""Deterministic ranking signals applied after Qwen's technical assessment."""
from __future__ import annotations

from dataclasses import replace
from datetime import datetime, timezone
from urllib.parse import urlsplit

from .models import BriefItem, NewsItem
from .sources import canonical_url

# These lists deliberately privilege primary sources while still allowing credible
# third-party reporting to surface. Keep them short and review changes in code.
OFFICIAL_DOMAINS = (
    "openai.com", "anthropic.com", "deepmind.google", "ai.google", "research.google",
    "huggingface.co", "nvidia.com", "developer.nvidia.com", "github.com", "arxiv.org",
    "microsoft.com", "aws.amazon.com", "meta.com",
)
TRUSTED_MEDIA_DOMAINS = (
    "reuters.com", "technologyreview.com", "thedecoder.com", "techcrunch.com", "venturebeat.com",
)
LOW_VALUE_DOMAINS = (
    "facebook.com", "quora.com", "reddit.com", "x.com", "twitter.com", "yahoo.com",
    "investing.com", "fool.com", "seekingalpha.com",
)


def _matches(domain: str, entries: tuple[str, ...]) -> bool:
    return any(domain == entry or domain.endswith(f".{entry}") for entry in entries)


def source_quality(url: str) -> float:
    domain = urlsplit(url).netloc.lower().removeprefix("www.")
    if _matches(domain, OFFICIAL_DOMAINS):
        return 1.0
    if _matches(domain, TRUSTED_MEDIA_DOMAINS):
        return 0.7
    if _matches(domain, LOW_VALUE_DOMAINS):
        return 0.0
    return 0.45


def freshness(published_at: datetime, now: datetime) -> float:
    age_hours = max(0.0, (now - published_at).total_seconds() / 3600)
    return max(0.0, 1.0 - age_hours / 48.0)


def rank_and_deduplicate(
    briefs: list[BriefItem], candidates: list[NewsItem], now: datetime | None = None
) -> list[BriefItem]:
    """Rank by technical value, source quality, cross-provider evidence, and freshness."""
    now = now or datetime.now(timezone.utc)
    candidates_by_url = {canonical_url(candidate.url): candidate for candidate in candidates}
    scored: list[BriefItem] = []
    for brief in briefs:
        candidate = candidates_by_url.get(canonical_url(brief.url))
        providers = candidate.providers if candidate else frozenset()
        provider_consensus = 1.0 if len(providers) >= 2 else 0.0
        final_score = (
            0.50 * (brief.score / 10.0)
            + 0.20 * source_quality(brief.url)
            + 0.15 * provider_consensus
            + 0.15 * freshness(brief.published_at, now)
        )
        scored.append(replace(brief, rank_score=round(final_score, 4)))

    # The model gives reports of one event an identical topic. Fall back to the
    # canonical URL if it cannot establish an event identity.
    selected: list[BriefItem] = []
    seen_topics: set[str] = set()
    for brief in sorted(scored, key=lambda item: item.rank_score, reverse=True):
        topic = brief.topic or canonical_url(brief.url)
        if topic in seen_topics:
            continue
        seen_topics.add(topic)
        selected.append(brief)
    return selected
