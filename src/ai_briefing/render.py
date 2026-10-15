from __future__ import annotations

import html
from datetime import datetime
from zoneinfo import ZoneInfo

from .models import BriefItem


def subject(now: datetime, timezone: str) -> str:
    return f"Daily AI Intelligence · {now.astimezone(ZoneInfo(timezone)):%Y-%m-%d}"


def plain_text(items: list[BriefItem], now: datetime, timezone: str) -> str:
    date = now.astimezone(ZoneInfo(timezone)).strftime("%Y-%m-%d")
    lines = [f"Daily AI Intelligence · {date}", "For internal reference only; based on approved public sources.", ""]
    if not items:
        return "\n".join(lines + ["No AI developments met the briefing threshold in the past day."])
    for index, item in enumerate(items, 1):
        lines.extend([f"{index}. [{item.category}] {item.headline}", f"   {item.summary}"])
        lines.extend([f"   Source: {item.source}", f"   {item.url}", ""])
    return "\n".join(lines).strip()


def email_html(items: list[BriefItem], now: datetime, timezone: str) -> str:
    date = now.astimezone(ZoneInfo(timezone)).strftime("%Y-%m-%d")
    cards = []
    for item in items:
        cards.append(
            '<section style="padding:16px 0;border-bottom:1px solid #e6e9ee">'
            f'<div><span style="font-size:12px;color:#52677f">{html.escape(item.category)}</span> '
            f'<a href="{html.escape(item.url, quote=True)}" style="color:#1155a3;font-size:16px;font-weight:650;text-decoration:none">{html.escape(item.headline)}</a></div>'
            f'<p style="margin:7px 0;color:#222;line-height:1.6">{html.escape(item.summary)}</p>'
            f'<p style="margin:8px 0 0;color:#748091;font-size:12px">Source: {html.escape(item.source)} · public link</p></section>'
        )
    body = "".join(cards) or '<p style="color:#607080">No AI developments met the briefing threshold in the past day.</p>'
    return (
        '<div style="max-width:680px;margin:auto;padding:28px;font-family:-apple-system,BlinkMacSystemFont,Segoe UI,Arial,sans-serif">'
        f'<h1 style="font-size:22px;margin:0;color:#102a43">Daily AI Intelligence</h1><p style="color:#607080;margin:6px 0 20px">{date} · Internal reference · Approved public sources</p>'
        f'{body}<footer style="padding-top:18px;color:#8895a7;font-size:12px">Summarised by the internal Qwen3.8-Next service; verify details against the original source.</footer></div>'
    )
