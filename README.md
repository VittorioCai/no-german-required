# English Job Agent for Germany 🇩🇪🔍

**English** | [简体中文](README.zh-CN.md)

**No German Required? Check before you apply.**

Finds and ranks English-friendly student jobs in Germany, detects hidden German
requirements, and sends a daily digest.

It scans English-friendly job sources daily, detects hidden German-language requirements
that keyword filters miss, scores each job against *your* profile with an LLM, and emails
you a short digest. Fork it, add your provider and notification secrets, done —
runs free on GitHub Actions.

## Why this exists

Every international student in Germany knows the trap: the job posting is in perfect
English, you spend an hour on the application, and then —
*"fließend Deutsch in Wort und Schrift erforderlich."*

**An English JD does not mean an English workplace.** Generic job boards can't tell the
difference. This agent reads the fine print for you:

- 🔍 **Two-stage language filter** — regex gate for obvious cases
  (`verhandlungssicher`, `C1`, `fluent German required`), then an LLM judgment with
  quoted evidence for the subtle ones
- 🎓 **Student-aware** — targets Werkstudent / Praktikum / internship roles and knows
  your German level (B1 ≠ zero: "German is a plus" jobs stay in)
- 📊 **Scored, not dumped** — every match comes with a 0-100 fit score, the working
  language, and red flags (unpaid, enrollment requirements, on-site 5 days…)
- 📬 **One digest a day** — email or Telegram; Top 10 matches plus 3 near-misses so
  you can tune your filters
- 📋 **Application tracker** — mark jobs as applied/interview/offer and they vanish
  from future digests
- 🆓 **Zero infrastructure** — GitHub Actions + your own LLM key
  (Anthropic / OpenAI / DeepSeek / any OpenAI-compatible endpoint)

## What it does NOT do

**No auto-apply.** Ever. Auto-application bots get accounts banned, waste recruiters'
time, and produce spray-and-pray applications that hurt you. This agent finds and
filters; *you* apply. It also only uses **public, no-auth APIs and career feeds**
([Arbeitnow](https://www.arbeitnow.com/api), Greenhouse, Lever, Ashby, Workday,
Personio, SmartRecruiters, and Recruitee) —
no scraping behind login walls, no ToS violations.

## Quickstart (5 minutes)

1. **Fork** this repo. Prefer a private repository when using a real profile or
   application notes. Public repositories expose `profile.yaml`, tracked application
   state, and committed job-match data to everyone.
2. **Edit [`profile.yaml`](profile.yaml)** — your roles, cities, German level, and a
   3-line CV summary
3. **Add repository secrets** (Settings → Secrets and variables → Actions → Secrets):

   | Secret | Value |
   |---|---|
   | `LLM_API_KEY` | your Anthropic / OpenAI / DeepSeek key |
   | `SMTP_USER` | your Gmail address |
   | `SMTP_PASS` | a [Gmail app password](https://myaccount.google.com/apppasswords) |

4. **Optional variables** (same page → Variables): `LLM_PROVIDER`
   (`anthropic` default / `openai` / `deepseek`), `LLM_MODEL`, `MAIL_TO`,
   `MAX_LLM_CALLS` (default 25/day to cap costs), `NOTIFY`
   (`email` default / `telegram` / `both` — Telegram needs
   `TELEGRAM_BOT_TOKEN` + `TELEGRAM_CHAT_ID` secrets, see
   [`src/notify/telegram.py`](src/notify/telegram.py)). Optional company intel is
   disabled by default; enable it with `ENABLE_COMPANY_INTEL=true`. Its
   `MAX_INTEL_CALLS` (default 3) is reserved inside the same total budget, and
   `COMPANY_INTEL_TTL_DAYS` (default 30) controls cache refreshes.
5. **Test it**: Actions tab → *Daily job scan* → *Run workflow*

Your digest runs at 06:00 UTC: approximately 07:00 German time in winter and 08:00
in summer. GitHub Actions schedules can occasionally start a little later.

### Run locally

```bash
pip install -r requirements.txt
cp .env.example .env        # fill in your keys
set -a; source .env; set +a # export the file for this shell
python -m src.main --dry-run   # no LLM calls, no email — see what passes the gate
python -m src.main             # full run
```

### Track your applications

```bash
python -m src.track add https://n26.com/en/careers/positions/12345   # marks as applied
python -m src.track add <url> interview "phone screen on Friday"
python -m src.track list
python -m src.track stats
```

Tracked jobs never reappear in your digest. Commit `data/applications.json`
to sync state with the GitHub Actions runs.

### Optional research and drafting helpers

Company intel adds a short, cached company briefing to email cards. It is **disabled by
default** because it uses extra LLM calls. With the defaults, enabling it reserves up to
3 of the daily 25 calls for intel, leaving 22 actual model-call slots for job judgments;
validation retries consume those slots and cached briefings use no call. Treat the summary
as orientation and verify important facts before an interview.

The cover-letter helper is manual and local. It drafts but never applies or sends:

```bash
python -m src.agents.draft --list
python -m src.agents.draft <job-url>       # English draft
python -m src.agents.draft <job-url> --de  # simple German draft
```

Drafts are saved as plain text under the gitignored `drafts/` directory and never overwrite an
existing file. The selected posting and your `cv_summary` are sent to your configured
LLM provider only when you run this command. `data/matches.json` stores job data, not
your applicant profile. The daily job judgment also sends `cv_summary` and job text to
that provider. These are focused helpers, not autonomous application agents.

## How it works

```
Arbeitnow API ──────────┐
Greenhouse/Lever/Ashby ─┤
Personio/Recruitee ─────┼─→ cross-source dedup ─→ rule gate ─→ LLM judge ─→ digest
SmartRecruiters ────────┤      (free)               (free)    (budget-capped)
Workday ────────────────┘
```

The LLM returns structured judgment per job:

```json
{
  "working_language": "English",
  "german_required": "nice-to-have",
  "language_confidence": 0.92,
  "evidence": "Our company language is English; German is a plus.",
  "match_score": 85,
  "red_flags": ["requires enrollment for 2+ more semesters"],
  "summary": "Strong fit: Werkstudent data role in Berlin, English-first team."
}
```

If a job needs more German than your `german_level`, the LLM subtracts 10-20 points
and adds a clear red flag. Strong matches remain visible so you can decide whether
the language stretch is worth applying for.

## What's covered (job sources)

Two kinds of sources, both public and auth-free:

- **[Arbeitnow](https://www.arbeitnow.com/english-speaking-jobs)** — a Germany-focused
  English-friendly job board, ~300 live postings, mostly startups and mid-size tech.
  Companies here change daily; you don't configure anything.
- **45 monitored companies** in [`data/companies.yaml`](data/companies.yaml), fetched
  directly from their ATS feeds:
  fintech (N26, Trade Republic, Solaris, Deutsche Bank...), consumer tech (HelloFresh,
  GetYourGuide, Flix, FreeNow, Scout24...), B2B software (Celonis, Contentful,
  commercetools, KONUX...), industrial (Airbus, thyssenkrupp Steel, ZEISS, BorgWarner,
  Zeppelin, Isar Aerospace), pharma (Pfizer, Moderna, GSK, IQVIA), plus Personio,
  SmartRecruiters, and Recruitee employers such as UnternehmerTUM, Scalable Capital,
  TWAICE, and neXenio.

**Not covered:** companies on SuccessFactors or fully custom career portals
(BMW, Mercedes-Benz, Audi, VW, Siemens, Bosch, SAP, DHL...). Their student roles
occasionally surface via Arbeitnow, but don't rely on it. Every company list entry
is one line — add your targets and open a PR.

## Make it yours (any major, any German level)

Everything personal lives in [`profile.yaml`](profile.yaml) — no code changes needed.
The default file targets a business/data student; here is how to adapt it:

- **Your field** → `field_keywords`. Mechanical engineering: `[mechanical, cad,
  simulation, automotive, manufacturing]`. Marketing: `[marketing, social media,
  content, seo, brand]`. Finance: `[finance, accounting, controlling, audit, m&a]`.
  Jobs must mention at least one keyword anywhere in the posting.
- **Role types** → `role_keywords`. Defaults cover Werkstudent / intern / Praktikum /
  thesis. Hunting full-time entry roles instead? Use `[graduate, junior, entry level,
  trainee]`.
- **Your German level** → `german_level: A1..C1`. This is the core feature: the LLM
  compares each job's *actual* language requirement (often hidden in fine print)
  against your level. With `apply_anyway: true` harder-language jobs still appear,
  penalized and red-flagged, so *you* decide; set it to `false` to hard-filter them.
- **Location** → `cities: [berlin, munich]` for specific cities, or `cities: []` +
  `germany_only: true` for all of Germany.
- **Volume vs. precision** → `min_score` (digest threshold), plus repo variables
  `MAX_LLM_CALLS` (total LLM budget/day), `TOP_N` / `NEAR_MISS_N` (digest length).
- **Your pitch** → `cv_summary`: 3-5 lines about your background. The LLM scores
  every job against this text — the more concrete, the better the ranking.

After profile changes, reset `data/seen.json` to `{"seen": []}` if you want the
already-processed backlog re-evaluated under the new rules.

## Good to know (visa & work rules) 📋

Not legal advice, but the rules the agent flags:

- **Werkstudent**: max **20 h/week** during lecture periods (full-time in semester breaks)
- **Non-EU students**: **140 full days** (or 280 half days) of work per year;
  Werkstudent jobs and mandatory internships (*Pflichtpraktikum*) count differently
- Many Werkstudent roles require current enrollment (*Immatrikulationsbescheinigung*)

## Contributing

See [`CONTRIBUTING.md`](CONTRIBUTING.md) for local setup, tests, and source-adapter
guidance. Please report security issues privately as described in
[`SECURITY.md`](SECURITY.md).

The most valuable PR: **add English-friendly companies** to
[`data/companies.yaml`](data/companies.yaml) — one line each, slug from the company's
careers URL (please verify the API responds before submitting). Also welcome: new
source adapters (`src/sources/`), better German-requirement patterns
(`src/filters/rules.py`), new notifiers (`src/notify/`).

## License

MIT
