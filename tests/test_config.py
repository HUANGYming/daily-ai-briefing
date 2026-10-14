import pytest

from ai_briefing.config import BriefingConfig, Feed


def test_config_rejects_no_sources():
    with pytest.raises(ValueError, match="至少需要"):
        BriefingConfig(feeds=[]).validate()


def test_config_rejects_invalid_item_limits():
    with pytest.raises(ValueError, match="max_items"):
        BriefingConfig(feeds=[Feed("approved", "https://example.test/feed")], max_items=9, candidate_limit=8).validate()
