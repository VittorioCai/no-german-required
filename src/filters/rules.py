"""Stage 1: free rule-based gate. Cheap, runs on every job.

Verdicts:
  reject  — hard German requirement or role/city mismatch
  pass    — candidate for LLM judging
"""
import re

# Hard German requirements — English JD does NOT mean English workplace.
GERMAN_REQUIRED = [
    r"fluen(t|cy)\s+(in\s+)?german",
    r"german\s*(language)?\s*(skills?|proficiency)?\s*(is|are)?\s*(a\s+)?(hard\s+)?(requirement|required|mandatory|essential|must)",
    r"(business|professional|native|full)\s*[- ]?\s*(level\s+)?german",
    r"german\s+(at\s+)?(minimum\s+)?(level\s+)?(c1|c2|b2)",
    r"(c1|c2)\s+(level\s+)?german",
    r"\bverhandlungssicher",
    r"\bmuttersprach\w*",
    r"deutsch\w*\s{0,3}(kenntnisse)?\s{0,3}\w{0,20}\s{0,3}(erforderlich|vorausgesetzt|voraussetzung|zwingend|notwendig)",
    r"flie(ß|ss)end\w*\s+(in\s+)?deutsch",
    r"sehr\s+gute\s+deutschkenntnisse",
]

# Positive signals — boost, and rescue borderline cases.
ENGLISH_FRIENDLY = [
    r"german\s+(is\s+)?(a\s+)?(nice|plus|bonus|advantage|not\s+required)",
    r"no\s+german\s+(required|needed|necessary)",
    r"english[- ](speaking|first|only)\s+(team|environment|company|workplace)?",
    r"(company|working|official|team)\s+language\s+(is\s+)?english",
    r"we\s+work\s+in\s+english",
]

_g = [re.compile(p, re.I) for p in GERMAN_REQUIRED]
_e = [re.compile(p, re.I) for p in ENGLISH_FRIENDLY]


# Words that start with a role keyword but are NOT roles.
_ROLE_STOPWORDS = {
    "international", "internationale", "internationaler", "internationales",
    "internal", "internally", "internet",
}


def _title_matches_role(title: str, roles: list) -> bool:
    for r in roles:
        for m in re.finditer(rf"\b{re.escape(r)}\w*", title):
            if m.group(0) not in _ROLE_STOPWORDS:
                return True
    return False


def _match_any(patterns, text):
    for p in patterns:
        m = p.search(text)
        if m:
            return m.group(0)
    return None


def gate(job, profile) -> tuple:
    """Returns (verdict, reason)."""
    text = f"{job.title}\n{job.description}"

    # 1. Role keywords must appear in the title. Word-start match so German
    # compounds work ("Praktikumsstelle", "Praktikantin", "Werkstudenten"),
    # with a stoplist so "intern" doesn't match "International"/"Internal".
    roles = [r.lower() for r in profile.get("role_keywords", [])]
    if roles and not _title_matches_role(job.title.lower(), roles):
        return "reject", "title does not match role keywords"

    # 2. Field keywords anywhere.
    fields = [f.lower() for f in profile.get("field_keywords", [])]
    if fields and not any(f in text.lower() for f in fields):
        return "reject", "no field keyword match"

    # 3. Location.
    cities = [c.lower() for c in profile.get("cities", [])]
    if cities and not any(c in job.location.lower() for c in cities):
        return "reject", f"location '{job.location}' not in target cities"

    # 4. Language gate.
    hit = _match_any(_g, text)
    if hit:
        friendly = _match_any(_e, text)
        if not friendly:
            return "reject", f"German required: “{hit.strip()}”"
        # Contradictory signals → let the LLM decide.
        return "pass", f"mixed signals: “{hit.strip()}” vs “{friendly.strip()}”"

    return "pass", "no German requirement detected"
