"""Stage 2: LLM judgment on jobs that survived the rule gate."""
from ..llm import complete_json

PROMPT = """You screen jobs for an international student in Germany whose German level is {german_level}.

Their profile:
{cv_summary}

They are looking for: {roles} positions in {fields}.

Analyze this job posting and answer in strict JSON (no markdown, no commentary):

{{
  "working_language": "English" | "German" | "unclear",
  "german_required": "none" | "nice-to-have" | "B1-B2" | "C1+",
  "evidence": "<short quote from the posting supporting your language judgment>",
  "match_score": <0-100, fit with the profile>,
  "red_flags": ["<e.g. requires enrollment ≥2 semesters, on-site 5 days, unpaid>"],
  "summary": "<one sentence: why this is or isn't a good match>"
}}

Rules:
- An English JD does NOT imply an English workplace. Look for explicit language cues.
- If german_required exceeds the student's level {german_level}, do NOT exclude the
  job: score it on actual fit, subtract 10-20 points, and add a red flag stating the
  required German level (e.g. "requires B2 German — above your A1"). A strong fit
  with a language stretch is still worth showing.
- Customer-facing roles in the German market usually need German even if unstated — flag it.

Job posting:
Title: {title}
Company: {company}
Location: {location}
---
{description}
"""


def judge(job, profile) -> dict:
    prompt = PROMPT.format(
        german_level=profile.get("german_level", "A2"),
        cv_summary=profile.get("cv_summary", ""),
        roles=", ".join(profile.get("role_keywords", [])),
        fields=", ".join(profile.get("field_keywords", [])),
        title=job.title, company=job.company,
        location=job.location, description=job.description[:5000],
    )
    try:
        result = complete_json(prompt)
        result.setdefault("match_score", 0)
        result.setdefault("red_flags", [])
        return result
    except Exception as e:
        print(f"[judge] {job.id} failed: {e}")
        return {"working_language": "unclear", "german_required": "unclear",
                "evidence": "", "match_score": 0, "red_flags": [f"LLM error: {e}"],
                "summary": "judgment failed"}
