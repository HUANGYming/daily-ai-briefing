from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path

from .config import load_config
from .emailer import recipients_from_env, send
from .llm import curate
from .render import email_html, plain_text, subject
from .sources import canonical_url, collect


def run(config_path: str | Path, dry_run: bool = False) -> int:
    config = load_config(config_path)
    now = datetime.now(timezone.utc)
    rss_candidates = collect(config.feeds, config.lookback_hours, config.max_per_feed, config.candidate_limit)
    from .search import collect as collect_search
    search_candidates = collect_search(config.search)
    candidates = []
    seen_urls: set[str] = set()
    for item in sorted(rss_candidates + search_candidates, key=lambda item: item.published_at, reverse=True):
        url = canonical_url(item.url)
        if url in seen_urls:
            continue
        seen_urls.add(url)
        candidates.append(item)
        if len(candidates) >= config.candidate_limit:
            break
    briefing = curate(candidates, config.minimum_score)[:config.max_items]
    mail_subject = subject(now, config.timezone)
    text = plain_text(briefing, now, config.timezone)
    if dry_run:
        print(mail_subject)
        print(text)
        return len(briefing)
    send(mail_subject, email_html(briefing, now, config.timezone), text, recipients_from_env())
    return len(briefing)
