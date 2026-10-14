from datetime import datetime, timezone

from ai_briefing.models import BriefItem
from ai_briefing.render import email_html, plain_text


ITEM = BriefItem("Official Lab", "Original", "https://example.test/a?x=1", datetime(2026, 1, 1, tzinfo=timezone.utc),
                 "New model release", "Supports <b>untrusted HTML</b>", "Consider it for internal assistant evaluation.", "model", 9)


def test_email_escapes_untrusted_model_content():
    html = email_html([ITEM], datetime(2026, 1, 2, tzinfo=timezone.utc), "Asia/Macau")
    assert "&lt;b&gt;untrusted HTML&lt;/b&gt;" in html
    assert "https://example.test/a?x=1".replace("&", "&amp;") in html


def test_text_contains_source_link():
    text = plain_text([ITEM], datetime(2026, 1, 2, tzinfo=timezone.utc), "Asia/Macau")
    assert "https://example.test/a?x=1" in text
