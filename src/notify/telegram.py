"""Daily digest via Telegram bot.

Setup: create a bot with @BotFather, get TELEGRAM_BOT_TOKEN; message the bot
once, then get your chat id from https://api.telegram.org/bot<token>/getUpdates
"""
import os
from urllib.parse import urlparse

import requests

MAX_LEN = 4000  # Telegram hard limit is 4096


def _esc(text: str) -> str:
    return text.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def _card(job, j) -> str:
    flags = ""
    if j.get("red_flags"):
        flags = "\n⚠ " + " · ".join(_esc(f) for f in j["red_flags"])
    parsed = urlparse(job.url)
    title = _esc(job.title)
    linked_title = f'<a href="{_esc(job.url)}">{title}</a>' if parsed.scheme in {"http", "https"} else title
    return (
        f"<b>{j['match_score']}/100</b> · {linked_title}\n"
        f"{_esc(job.company)} · {_esc(job.location)} · "
        f"lang: {_esc(str(j.get('working_language', '?')))} "
        f"({round(float(j.get('language_confidence', 0)) * 100)}% confidence) · "
        f"German: {_esc(str(j.get('german_required', '?')))}\n"
        f"{_esc(j.get('summary', ''))}{flags}"
    )


def _send(token: str, chat_id: str, text: str):
    resp = requests.post(
        f"https://api.telegram.org/bot{token}/sendMessage",
        json={"chat_id": chat_id, "text": text, "parse_mode": "HTML",
              "disable_web_page_preview": True},
        timeout=30,
    )
    resp.raise_for_status()


def send_digest(top: list, near_misses: list, stats: dict):
    token = os.environ["TELEGRAM_BOT_TOKEN"]
    chat_id = os.environ["TELEGRAM_CHAT_ID"]

    blocks = [f"🇩🇪 <b>{len(top)} matches</b> · {stats['total']} jobs scanned, "
              f"{stats['judged']} judged"]
    blocks += [_card(job, j) for job, j in top]
    if near_misses:
        blocks.append("<i>Close, but filtered out:</i>")
        blocks += [_card(job, j) for job, j in near_misses]

    # Pack blocks into as few messages as possible.
    buf = ""
    for b in blocks:
        if len(buf) + len(b) + 2 > MAX_LEN:
            _send(token, chat_id, buf)
            buf = b
        else:
            buf = f"{buf}\n\n{b}" if buf else b
    if buf:
        _send(token, chat_id, buf)
    print(f"[telegram] digest sent to chat {chat_id}")
