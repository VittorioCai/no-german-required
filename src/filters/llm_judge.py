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
  "language_confidence": <0.0-1.0, confidence in the language judgment>,
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
    error = None
    for _ in range(2):
        try:
            return _validate_judgment(complete_json(prompt))
        except Exception as e:
            error = e
    print(f"[judge] {job.id} failed after retry: {error}")
    return {"working_language": "unclear", "german_required": "unclear",
            "language_confidence": 0, "evidence": "", "match_score": 0,
            "red_flags": [f"LLM error: {error}"], "summary": "judgment failed"}


def _validate_judgment(result: dict) -> dict:
    if not isinstance(result, dict):
        raise ValueError("judgment must be a JSON object")
    if result.get("working_language") not in {"English", "German", "unclear"}:
        raise ValueError("invalid working_language")
    if result.get("german_required") not in {"none", "nice-to-have", "B1-B2", "C1+"}:
        raise ValueError("invalid german_required")
    for field in ("evidence", "summary"):
        if not isinstance(result.get(field), str):
            raise ValueError(f"{field} must be a string")
    score = result.get("match_score")
    if isinstance(score, bool) or not isinstance(score, (int, float)) or not 0 <= score <= 100:
        raise ValueError("match_score must be a number from 0 to 100")
    flags = result.get("red_flags")
    if not isinstance(flags, list) or not all(isinstance(flag, str) for flag in flags):
        raise ValueError("red_flags must be a list of strings")
    confidence = result.get("language_confidence")
    if isinstance(confidence, bool) or not isinstance(confidence, (int, float)) \
            or not 0 <= confidence <= 1:
        raise ValueError("language_confidence must be a number from 0 to 1")
    return result
