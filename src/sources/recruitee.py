"""Public Recruitee Careers Site feeds."""
import html
import re

import requests

from .base import Job, Source


def _strip_html(value: str) -> str:
    value = re.sub(r"<[^>]+>", " ", value or "")
    return html.unescape(re.sub(r"\s+", " ", value)).strip()


class RecruiteeSource(Source):
    name = "recruitee"

    def __init__(self, companies: list):
        self.companies = [company for company in companies if company.get("ats") == "recruitee"]

    def fetch(self) -> list:
        jobs = []
        for company in self.companies:
            try:
                found = self._company(company)
                jobs.extend(found)
                print(f"[recruitee] {company['name']}: {len(found)} jobs")
            except Exception as error:
                print(f"[recruitee] {company['name']} skipped ({error})")
        return jobs

    def _company(self, company: dict) -> list:
        slug = company["slug"]
        response = requests.get(f"https://{slug}.recruitee.com/api/offers/", timeout=30)
        response.raise_for_status()
        jobs = []
        for offer in response.json().get("offers", []):
            english = (offer.get("translations") or {}).get("en") or {}
            locations = offer.get("locations") or []
            location = locations[0] if locations else {}
            country = location.get("country_code") or offer.get("country_code", "")
            place = ", ".join(part for part in (location.get("city") or offer.get("city", ""),
                                                country) if part)
            description = english.get("description", offer.get("description", ""))
            requirements = english.get("requirements", offer.get("requirements", ""))
            jobs.append(Job(
                id=f"recruitee:{slug}:{offer.get('id', offer.get('guid', ''))}",
                title=english.get("title", offer.get("title", "")),
                company=company["name"],
                location=place,
                url=offer.get("careers_url", ""),
                description=f"{_strip_html(description)} {_strip_html(requirements)}".strip()[:6000],
                source="recruitee",
                country=country,
            ))
        return jobs
