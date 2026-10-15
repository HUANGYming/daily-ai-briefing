from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from zoneinfo import ZoneInfo

import yaml


@dataclass(frozen=True)
class Feed:
    name: str
    url: str


@dataclass(frozen=True)
class SearchConfig:
    enabled: bool = False
    providers: list[str] = field(default_factory=lambda: ["tavily"])
    queries: list[str] | None = None
    max_results_per_query: int = 5
    search_depth: str = "basic"
    time_range: str = "day"

    def validate(self) -> None:
        if not self.enabled:
            return
        supported = {"tavily", "brave_llm_context"}
        if not self.providers or any(provider not in supported for provider in self.providers):
            raise ValueError("搜索服务仅支持 tavily 或 brave_llm_context")
        if len(set(self.providers)) != len(self.providers):
            raise ValueError("搜索服务不能重复配置")
        if not self.queries or not all(query.strip() for query in self.queries):
            raise ValueError("启用搜索时必须至少配置一个 query")
        if not 1 <= self.max_results_per_query <= 20:
            raise ValueError("max_results_per_query 必须在 1 到 20 之间")
        if self.search_depth not in {"basic", "advanced", "fast", "ultra-fast"}:
            raise ValueError("search_depth 不受支持")
        if self.time_range not in {"day", "week", "month", "year"}:
            raise ValueError("time_range 不受支持")


@dataclass(frozen=True)
class BriefingConfig:
    feeds: list[Feed]
    lookback_hours: int = 28
    max_per_feed: int = 10
    candidate_limit: int = 45
    max_items: int = 8
    minimum_score: int = 6
    timezone: str = "Asia/Macau"
    search: SearchConfig = SearchConfig()

    def validate(self) -> None:
        if not self.feeds:
            raise ValueError("至少需要配置一个批准的数据源")
        if not 1 <= self.max_items <= self.candidate_limit:
            raise ValueError("max_items 必须在 1 到 candidate_limit 之间")
        if not 0 <= self.minimum_score <= 10:
            raise ValueError("minimum_score 必须在 0 到 10 之间")
        ZoneInfo(self.timezone)
        self.search.validate()


def load_config(path: str | Path) -> BriefingConfig:
    raw = yaml.safe_load(Path(path).read_text(encoding="utf-8")) or {}
    feeds = [Feed(name=str(item["name"]), url=str(item["url"])) for item in raw.get("feeds", [])]
    raw_search = raw.get("search", {}) or {}
    search = SearchConfig(
        enabled=bool(raw_search.get("enabled", False)),
        providers=[str(provider) for provider in raw_search.get(
            "providers", [raw_search.get("provider", "tavily")]
        )],
        queries=[str(query) for query in raw_search.get("queries", [])],
        max_results_per_query=int(raw_search.get("max_results_per_query", 5)),
        search_depth=str(raw_search.get("search_depth", "basic")),
        time_range=str(raw_search.get("time_range", "day")),
    )
    cfg = BriefingConfig(
        feeds=feeds,
        lookback_hours=int(raw.get("lookback_hours", 28)),
        max_per_feed=int(raw.get("max_per_feed", 10)),
        candidate_limit=int(raw.get("candidate_limit", 45)),
        max_items=int(raw.get("max_items", 8)),
        minimum_score=int(raw.get("minimum_score", 6)),
        timezone=str(raw.get("timezone", "Asia/Macau")),
        search=search,
    )
    cfg.validate()
    return cfg
