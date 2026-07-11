"""no-german-required: daily pipeline.

fetch → dedup → rule gate → LLM judge → email digest → persist seen ids
Run: python -m src.main [--dry-run]
"""
import json
import os
import sys

import yaml

from .filters.rules import gate
from .sources.arbeitnow import ArbeitnowSource
from .sources.ats import ATSSource

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SEEN_PATH = os.path.join(ROOT, "data", "seen.json")
MAX_LLM_CALLS = int(os.environ.get("MAX_LLM_CALLS") or "25")
TOP_N = int(os.environ.get("TOP_N") or "10")
NEAR_MISS_N = int(os.environ.get("NEAR_MISS_N") or "3")


def load_yaml(path):
    with open(path, encoding="utf-8") as f:
        return yaml.safe_load(f)


def load_seen():
    try:
        with open(SEEN_PATH, encoding="utf-8") as f:
            return set(json.load(f)["seen"])
    except (FileNotFoundError, json.JSONDecodeError, KeyError):
        return set()


def save_seen(seen: set):
    os.makedirs(os.path.dirname(SEEN_PATH), exist_ok=True)
    with open(SEEN_PATH, "w", encoding="utf-8") as f:
        json.dump({"seen": sorted(seen)[-20000:]}, f, indent=0)


def run(dry_run: bool = False):
    profile = load_yaml(os.path.join(ROOT, "profile.yaml"))
    companies = load_yaml(os.path.join(ROOT, "data", "companies.yaml"))["companies"]

    from .track import tracked_urls
    seen, applied = load_seen(), tracked_urls()

    # 1. Fetch (Workday skips already-seen ids to save per-job detail requests)
    from .sources.workday import WorkdaySource
    jobs = []
    for source in (ArbeitnowSource(), ATSSource(companies),
                   WorkdaySource(companies, skip_ids=seen)):
        jobs.extend(source.fetch())
    stats = {"total": len(jobs)}

    # 2. Dedup (seen ids + already-applied URLs)
    fresh = [j for j in jobs if j.id not in seen and j.url not in applied]
    print(f"[dedup] {len(fresh)} new of {len(jobs)} ({len(applied)} tracked applications excluded)")

    # 3. Rule gate
    candidates, rejected = [], 0
    for job in fresh:
        verdict, reason = gate(job, profile)
        if verdict == "pass":
            candidates.append(job)
        else:
            rejected += 1
    stats["gated"] = len(candidates)
    print(f"[gate] {len(candidates)} passed, {rejected} rejected")

    if dry_run:
        for job in candidates[:20]:
            print(f"  PASS  {job.title} @ {job.company} ({job.location})")
        return

    # 4. LLM judge (budget-capped)
    from .filters.llm_judge import judge
    judged = [(job, judge(job, profile)) for job in candidates[:MAX_LLM_CALLS]]
    stats["judged"] = len(judged)
    judged.sort(key=lambda x: x[1]["match_score"], reverse=True)

    threshold = profile.get("min_score", 60)
    top = [(j, r) for j, r in judged if r["match_score"] >= threshold][:TOP_N]
    near = [(j, r) for j, r in judged if 0 < r["match_score"] < threshold][:NEAR_MISS_N]

    # 5. Notify (NOTIFY=email|telegram|both, default email)
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

    # 6. Persist — only successfully judged jobs count as seen; failed judgments
    # (e.g. bad API key) and unjudged jobs retry tomorrow.
    seen |= {job.id for job, r in judged
             if not any(str(f).startswith("LLM error") for f in r.get("red_flags", []))}
    seen |= {job.id for job in fresh if gate(job, profile)[0] == "reject"}
    save_seen(seen)
    print("[done]")


if __name__ == "__main__":
    run(dry_run="--dry-run" in sys.argv)
