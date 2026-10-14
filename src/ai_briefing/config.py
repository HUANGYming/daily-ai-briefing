from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from zoneinfo import ZoneInfo

import yaml


@dataclass(frozen=True)
class Feed:
    name: str
    url: str


@dataclass(frozen=True)
class BriefingConfig:
    feeds: list[Feed]
    lookback_hours: int = 28
    max_per_feed: int = 10
    candidate_limit: int = 45
    max_items: int = 8
    minimum_score: int = 6
    timezone: str = "Asia/Macau"

    def validate(self) -> None:
        if not self.feeds:
            raise ValueError("至少需要配置一个批准的数据源")
        if not 1 <= self.max_items <= self.candidate_limit:
            raise ValueError("max_items 必须在 1 到 candidate_limit 之间")
        if not 0 <= self.minimum_score <= 10:
            raise ValueError("minimum_score 必须在 0 到 10 之间")
        ZoneInfo(self.timezone)


def load_config(path: str | Path) -> BriefingConfig:
    raw = yaml.safe_load(Path(path).read_text(encoding="utf-8")) or {}
    feeds = [Feed(name=str(item["name"]), url=str(item["url"])) for item in raw.get("feeds", [])]
    cfg = BriefingConfig(
        feeds=feeds,
        lookback_hours=int(raw.get("lookback_hours", 28)),
        max_per_feed=int(raw.get("max_per_feed", 10)),
        candidate_limit=int(raw.get("candidate_limit", 45)),
        max_items=int(raw.get("max_items", 8)),
        minimum_score=int(raw.get("minimum_score", 6)),
        timezone=str(raw.get("timezone", "Asia/Macau")),
    )
    cfg.validate()
    return cfg
