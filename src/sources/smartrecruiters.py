"""Public SmartRecruiters company posting feeds."""
import html
import re

import requests

from .base import Job, Source

TITLE_PATTERNS = [re.compile(pattern, re.I) for pattern in (
    r"\bwerkstud\w*", r"\bworking student\b", r"\bintern(ship)?s?\b",
    r"\bpraktik\w*", r"\bthesis\b", r"\bstudent assistant\b",
)]


def _strip_html(value: str) -> str:
    value = re.sub(r"<[^>]+>", " ", value or "")
    return html.unescape(re.sub(r"\s+", " ", value)).strip()


class SmartRecruitersSource(Source):
    name = "smartrecruiters"

    def __init__(self, companies: list, max_details: int = 40, max_postings: int = 500):
        self.companies = [company for company in companies
                          if company.get("ats") == "smartrecruiters"]
        self.max_details = max_details
        self.max_postings = max_postings

    def fetch(self) -> list:
        jobs = []
        for company in self.companies:
            try:
                found = self._company(company)
                jobs.extend(found)
                print(f"[smartrecruiters] {company['name']}: {len(found)} student jobs")
            except Exception as error:
                print(f"[smartrecruiters] {company['name']} skipped ({error})")
        return jobs

    def _company(self, company: dict) -> list:
        slug = company["slug"]
        endpoint = f"https://api.smartrecruiters.com/v1/companies/{slug}/postings"
        postings, offset, limit = [], 0, 100
        while offset < self.max_postings:
            page_limit = min(limit, self.max_postings - offset)
            response = requests.get(endpoint, params={"limit": page_limit, "offset": offset,
                                                       "country": "de"}, timeout=30)
            response.raise_for_status()
            payload = response.json()
            page = payload.get("content", [])
            postings.extend(page)
            offset += len(page)
            if not page or offset >= payload.get("totalFound", 0):
                break

        candidates = [posting for posting in postings
                      if (posting.get("location") or {}).get("country", "").lower() == "de"
                      and any(pattern.search(posting.get("name", ""))
                              for pattern in TITLE_PATTERNS)]
        jobs = []
        for posting in candidates[:self.max_details]:
            try:
                response = requests.get(posting["ref"], timeout=30)
                response.raise_for_status()
                detail = response.json()
                sections = (detail.get("jobAd") or {}).get("sections") or {}
                description = " ".join(_strip_html(section.get("text", ""))
                                       for section in sections.values() if isinstance(section, dict))
                location = detail.get("location") or posting.get("location") or {}
                jobs.append(Job(
                    id=f"smartrecruiters:{slug}:{detail.get('id', posting.get('id', ''))}",
                    title=detail.get("name", posting.get("name", "")),
                    company=company["name"],
                    location=location.get("fullLocation", ""),
                    url=detail.get("postingUrl", ""),
                    description=description[:6000],
                    source="smartrecruiters",
                    country="DE",
                ))
            except Exception as error:
                print(f"[smartrecruiters] {company['name']} detail skipped ({error})")
        return jobs
