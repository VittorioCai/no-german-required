"""Workday career sites (big corporates: Airbus, Deutsche Bank, ZEISS, ...).

Workday exposes a semi-public JSON API used by its own career pages:
  POST https://{tenant}.wd{N}.myworkdayjobs.com/wday/cxs/{tenant}/{site}/jobs
       body: {"appliedFacets": {}, "limit": 20, "offset": 0, "searchText": "..."}
  GET  .../wday/cxs/{tenant}/{site}{externalPath}   -> job description

Finding a company's tenant/site: open their careers page, the URL looks like
  https://{tenant}.wd{N}.myworkdayjobs.com/{locale?}/{site}/...
"""
import html
import re

import requests

from ..filters.rules import GERMANY_HINTS
from .base import Job, Source

SEARCH_TERMS = ["werkstudent", "working student", "intern", "praktikum", "thesis"]
PAGE, MAX_OFFSET = 20, 100  # up to 5 pages per search term


def _strip_html(text: str) -> str:
    text = re.sub(r"<[^>]+>", " ", text or "")
    return html.unescape(re.sub(r"\s+", " ", text)).strip()


def _german(locations_text: str) -> bool:
    loc = (locations_text or "").lower()
    return any(h in loc for h in GERMANY_HINTS) or "locations" in loc  # "N Locations" → check later


class WorkdaySource(Source):
    name = "workday"

    def __init__(self, companies: list, skip_ids: set = None, max_details: int = 40):
        self.companies = [c for c in companies if c.get("ats") == "workday"]
        self.skip_ids = skip_ids or set()
        self.max_details = max_details  # detail requests per company per run

    def fetch(self) -> list:
        jobs = []
        for c in self.companies:
            try:
                found = self._company(c)
                jobs.extend(found)
            except Exception as e:
                print(f"[workday] {c['name']} skipped ({e})")
        return jobs

    def _company(self, c) -> list:
        base = f"https://{c['tenant']}.wd{c['wd']}.myworkdayjobs.com/wday/cxs/{c['tenant']}/{c['site']}"
        postings = {}
        for term in SEARCH_TERMS:
            offset = 0
            while offset < MAX_OFFSET:
                resp = requests.post(
                    f"{base}/jobs",
                    json={"appliedFacets": {}, "limit": PAGE, "offset": offset,
                          "searchText": term},
                    timeout=30,
                )
                resp.raise_for_status()
                data = resp.json()
                page = data.get("jobPostings", [])
                for p in page:
                    if p.get("externalPath"):
                        postings[p["externalPath"]] = p
                offset += PAGE
                if not page or offset >= data.get("total", 0):
                    break

        # Global boards list worldwide jobs; keep German locations, skip seen ids.
        candidates = [
            (path, p) for path, p in postings.items()
            if f"workday:{c['tenant']}:{path}" not in self.skip_ids
            and _german(p.get("locationsText", ""))
        ]
        out = []
        for path, p in candidates[: self.max_details]:
            desc, loc = self._detail(base, path)
            out.append(Job(
                id=f"workday:{c['tenant']}:{path}",
                title=p.get("title", ""),
                company=c["name"],
                location=loc or p.get("locationsText", ""),
                url=f"https://{c['tenant']}.wd{c['wd']}.myworkdayjobs.com/{c['site']}{path}",
                description=desc,
                source="workday",
            ))
        print(f"[workday] {c['name']}: {len(postings)} student posts, "
              f"{len(candidates)} German+new, {len(out)} fetched")
        return out

    @staticmethod
    def _detail(base: str, path: str):
        try:
            resp = requests.get(f"{base}{path}", timeout=30)
            resp.raise_for_status()
            info = resp.json().get("jobPostingInfo", {})
            return _strip_html(info.get("jobDescription", ""))[:6000], info.get("location", "")
        except Exception:
            return "", ""
