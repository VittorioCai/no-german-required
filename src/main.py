"""English Job Agent for Germany: daily pipeline.

fetch → dedup → rule gate → LLM judge → email digest → persist seen ids
Run: python -m src.main [--dry-run]
"""
import json
import os
import re
import sys
from collections import Counter
from datetime import datetime, timezone
from urllib.parse import parse_qsl, urlencode, urlsplit, urlunsplit

import yaml

from .filters.rules import gate, pre_score
from .sources.arbeitnow import ArbeitnowSource
from .sources.ats import ATSSource
from .sources.personio import PersonioSource
from .sources.recruitee import RecruiteeSource
from .sources.smartrecruiters import SmartRecruitersSource

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SEEN_PATH = os.path.join(ROOT, "data", "seen.json")
MAX_LLM_CALLS = int(os.environ.get("MAX_LLM_CALLS") or "25")
TOP_N = int(os.environ.get("TOP_N") or "10")
NEAR_MISS_N = int(os.environ.get("NEAR_MISS_N") or "3")
TRACKING_PARAMS = {"source", "ref", "referrer", "gh_src", "lever-source"}


def load_yaml(path):
    with open(path, encoding="utf-8") as f:
        return yaml.safe_load(f)


def load_seen():
    try:
        with open(SEEN_PATH, encoding="utf-8") as f:
            records = json.load(f)["seen"]
        seen = {}
        for record in records:
            if isinstance(record, str):
                seen[record] = "1970-01-01T00:00:00+00:00"
            elif isinstance(record, dict) and isinstance(record.get("id"), str) \
                    and isinstance(record.get("seen_at"), str):
                seen[record["id"]] = record["seen_at"]
        return seen
    except (FileNotFoundError, json.JSONDecodeError, KeyError, TypeError):
        return {}


def save_seen(seen: dict):
    os.makedirs(os.path.dirname(SEEN_PATH), exist_ok=True)
    newest = sorted(seen.items(), key=lambda item: item[1])[-20000:]
    with open(SEEN_PATH, "w", encoding="utf-8") as f:
        json.dump({"seen": [{"id": job_id, "seen_at": seen_at}
                            for job_id, seen_at in newest]}, f, indent=0)


def _canonical_url(url: str) -> str:
    try:
        parts = urlsplit(url)
        if parts.scheme not in {"http", "https"} or not parts.netloc:
            return ""
        query = [(key, value) for key, value in parse_qsl(parts.query)
                 if not key.lower().startswith("utm_") and key.lower() not in TRACKING_PARAMS]
        return urlunsplit((parts.scheme.lower(), parts.netloc.lower(),
                           parts.path.rstrip("/"), urlencode(sorted(query)), ""))
    except ValueError:
        return ""


def _normalized(value: str) -> str:
    return " ".join(re.sub(r"[^\w]+", " ", value or "", flags=re.UNICODE).lower().split())


def deduplicate_jobs(jobs: list) -> list:
    """Collapse cross-source duplicates, preferring first-party and fuller records."""
    parents = list(range(len(jobs)))

    def find(index):
        while parents[index] != index:
            parents[index] = parents[parents[index]]
            index = parents[index]
        return index

    def union(left, right):
        left, right = find(left), find(right)
        if left != right:
            parents[max(left, right)] = min(left, right)

    by_url, by_signature = {}, {}
    for index, job in enumerate(jobs):
        url_key = _canonical_url(job.url)
        signature = tuple(_normalized(value) for value in (job.company, job.title, job.location))
        signature_key = signature if all(signature) else None
        if url_key:
            if url_key in by_url:
                union(index, by_url[url_key])
            else:
                by_url[url_key] = index
        if signature_key:
            if signature_key in by_signature:
                union(index, by_signature[signature_key])
            else:
                by_signature[signature_key] = index

    groups = {}
    for index, job in enumerate(jobs):
        groups.setdefault(find(index), []).append(job)
    return [max(group, key=lambda job: (job.source != "arbeitnow",
                                        len(job.description or "")))
            for group in groups.values()]


def run(dry_run: bool = False):
    profile = load_yaml(os.path.join(ROOT, "profile.yaml"))
    companies = load_yaml(os.path.join(ROOT, "data", "companies.yaml"))["companies"]

    from .track import tracked_urls
    seen, applied = load_seen(), tracked_urls()

    # 1. Fetch (Workday skips already-seen ids to save per-job detail requests)
    from .sources.workday import WorkdaySource
    jobs = []
    for source in (ATSSource(companies), PersonioSource(companies),
                   SmartRecruitersSource(companies), RecruiteeSource(companies),
                   WorkdaySource(companies, skip_ids=seen), ArbeitnowSource()):
        jobs.extend(source.fetch())
    fetched = len(jobs)
    jobs = deduplicate_jobs(jobs)
    stats = {"fetched": fetched, "total": len(jobs)}
    print(f"[cross-dedup] {len(jobs)} unique of {fetched} fetched")

    # 2. Dedup (seen ids + already-applied URLs)
    fresh = [j for j in jobs if j.id not in seen and j.url not in applied]
    print(f"[dedup] {len(fresh)} new of {len(jobs)} ({len(applied)} tracked applications excluded)")

    # 3. Rule gate
    candidates, rejected_ids, rejection_reasons = [], set(), Counter()
    for job in fresh:
        verdict, reason = gate(job, profile)
        if verdict == "pass":
            candidates.append(job)
        else:
            rejected_ids.add(job.id)
            rejection_reasons[reason] += 1
    stats["gated"] = len(candidates)
    print(f"[gate] {len(candidates)} passed, {len(rejected_ids)} rejected")
    for reason, count in sorted(rejection_reasons.items(), key=lambda item: (-item[1], item[0])):
        print(f"  REJECT {count:4}  {reason}")

    if dry_run:
        for job in candidates[:20]:
            print(f"  PASS  {job.title} @ {job.company} ({job.location})")
        return

    # 4. LLM judge (budget-capped)
    from .filters.llm_judge import judge
    candidates.sort(key=lambda job: pre_score(job, profile), reverse=True)
    judged = [(job, judge(job, profile)) for job in candidates[:MAX_LLM_CALLS]]
    stats["judged"] = len(judged)
    judged.sort(key=lambda x: x[1]["match_score"], reverse=True)

    threshold = profile.get("min_score", 60)
    top = [(j, r) for j, r in judged if r["match_score"] >= threshold][:TOP_N]
    near = [(j, r) for j, r in judged if 0 < r["match_score"] < threshold][:NEAR_MISS_N]

    # 5. Persist before external notifications. Successfully judged jobs should
    # not consume another paid call if a notification provider is unavailable.
    now = datetime.now(timezone.utc).isoformat()
    for job, result in judged:
        if not any(str(flag).startswith("LLM error") for flag in result.get("red_flags", [])):
            seen[job.id] = now
    for job_id in rejected_ids:
        seen[job_id] = now
    save_seen(seen)

    # 6. Notify (NOTIFY=email|telegram|both, default email)
    if top or near:
        channels = os.environ.get("NOTIFY", "email").lower()
        if channels in ("email", "both"):
            from .notify.email import send_digest as send_email
            send_email(top, near, stats)
        if channels in ("telegram", "both"):
            from .notify.telegram import send_digest as send_tg
            send_tg(top, near, stats)
    else:
        print("[notify] nothing to send today")

    print("[done]")


if __name__ == "__main__":
    run(dry_run="--dry-run" in sys.argv)
