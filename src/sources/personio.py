"""Public Personio XML career feeds."""
import html
import re
import xml.etree.ElementTree as ET

import requests

from .base import Job, Source


def _text(node, path: str) -> str:
    value = node.findtext(path)
    return value.strip() if value else ""


def _strip_html(value: str) -> str:
    value = html.unescape(value or "")
    value = re.sub(r"<[^>]+>", " ", value)
    return html.unescape(re.sub(r"\s+", " ", value)).strip()


class PersonioSource(Source):
    name = "personio"

    def __init__(self, companies: list):
        self.companies = [company for company in companies if company.get("ats") == "personio"]

    def fetch(self) -> list:
        jobs = []
        for company in self.companies:
            try:
                found = self._company(company)
                jobs.extend(found)
                print(f"[personio] {company['name']}: {len(found)} jobs")
            except Exception as error:
                print(f"[personio] {company['name']} skipped ({error})")
        return jobs

    def _company(self, company: dict) -> list:
        slug = company["slug"]
        response = requests.get(f"https://{slug}.jobs.personio.de/xml?language=en", timeout=30)
        response.raise_for_status()
        root = ET.fromstring(response.content)
        jobs = []
        for position in root.findall("position"):
            job_id = _text(position, "id")
            if not job_id:
                continue
            sections = [_strip_html(value.text or "")
                        for value in position.findall("./jobDescriptions/jobDescription/value")]
            jobs.append(Job(
                id=f"personio:{slug}:{job_id}",
                title=_text(position, "name"),
                company=company["name"],
                location=_text(position, "office"),
                url=f"https://{slug}.jobs.personio.de/job/{job_id}?language=en",
                description=" ".join(section for section in sections if section)[:6000],
                source="personio",
                country="DE",
            ))
        return jobs
