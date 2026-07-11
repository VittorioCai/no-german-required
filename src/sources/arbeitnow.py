"""Arbeitnow public job board API — English-speaking jobs in Germany.

Docs: https://www.arbeitnow.com/api  (no auth required)
"""
import html
import re

import requests

from .base import Job, Source

API = "https://www.arbeitnow.com/api/job-board-api"


def _strip_html(text: str) -> str:
    text = re.sub(r"<[^>]+>", " ", text or "")
    return html.unescape(re.sub(r"\s+", " ", text)).strip()


class ArbeitnowSource(Source):
    name = "arbeitnow"

    def __init__(self, max_pages: int = 3):
        self.max_pages = max_pages

    def fetch(self) -> list:
        jobs, url = [], API
        for _ in range(self.max_pages):
            try:
                resp = requests.get(url, timeout=30)
                resp.raise_for_status()
                payload = resp.json()
            except Exception as e:
                print(f"[arbeitnow] fetch failed: {e}")
                break
            for j in payload.get("data", []):
                jobs.append(Job(
                    id=f"arbeitnow:{j['slug']}",
                    title=j.get("title", ""),
                    company=j.get("company_name", ""),
                    location=j.get("location", "") + (" (remote)" if j.get("remote") else ""),
                    url=j.get("url", ""),
                    description=_strip_html(j.get("description", ""))[:6000],
                    source=self.name,
                    tags=j.get("tags", []) + j.get("job_types", []),
                    country="DE",  # Arbeitnow is a Germany-focused board
                ))
            url = (payload.get("links") or {}).get("next")
            if not url:
                break
        print(f"[arbeitnow] {len(jobs)} jobs")
        return jobs
