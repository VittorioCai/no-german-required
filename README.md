# no-german-required 🇩🇪🚫🗣️

**English** | [简体中文](README.zh-CN.md)

**A job-hunting agent for international students in Germany who don't speak fluent German.**

It scans English-friendly job sources daily, detects hidden German-language requirements
that keyword filters miss, scores each job against *your* profile with an LLM, and emails
you a short digest. Fork it, add two secrets, done — runs free on GitHub Actions.

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
- 📬 **One digest a day** — email or Telegram; top 5 matches plus 3 near-misses so
  you can tune your filters
- 📋 **Application tracker** — mark jobs as applied/interview/offer and they vanish
  from future digests
- 🆓 **Zero infrastructure** — GitHub Actions + your own LLM key
  (Anthropic / OpenAI / DeepSeek / any OpenAI-compatible endpoint)

## What it does NOT do

**No auto-apply.** Ever. Auto-application bots get accounts banned, waste recruiters'
time, and produce spray-and-pray applications that hurt you. This agent finds and
filters; *you* apply. It also only uses **public, no-auth APIs**
([Arbeitnow](https://www.arbeitnow.com/api), Greenhouse/Lever/Ashby public boards) —
no scraping behind login walls, no ToS violations.

## Quickstart (5 minutes)

1. **Fork** this repo (keep it public for free Actions minutes, or private with your quota)
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
   [`src/notify/telegram.py`](src/notify/telegram.py))
5. **Test it**: Actions tab → *Daily job scan* → *Run workflow*

Your digest arrives every morning at ~7:00 German time.

### Run locally

```bash
pip install -r requirements.txt
cp .env.example .env        # fill in your keys
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

## How it works

```
Arbeitnow API ──┐
ATS feeds ──────┼─→ dedup ─→ rule gate ─→ LLM judge ─→ email digest
(Greenhouse/    │  (seen.json)  (free)    (budget-capped)  (top N + near misses)
 Ashby, 19 cos) │
Workday ────────┘
(Airbus, Deutsche Bank, ZEISS, thyssenkrupp, Pfizer, ...)
```

The LLM returns structured judgment per job:

```json
{
  "working_language": "English",
  "german_required": "nice-to-have",
  "evidence": "Our company language is English; German is a plus.",
  "match_score": 85,
  "red_flags": ["requires enrollment for 2+ more semesters"],
  "summary": "Strong fit: Werkstudent data role in Berlin, English-first team."
}
```

If a job needs more German than your `german_level`, its score is capped at 30 —
it lands in "near misses" instead of your inbox headline.

## Good to know (visa & work rules) 📋

Not legal advice, but the rules the agent flags:

- **Werkstudent**: max **20 h/week** during lecture periods (full-time in semester breaks)
- **Non-EU students**: **140 full days** (or 280 half days) of work per year;
  Werkstudent jobs and mandatory internships (*Pflichtpraktikum*) count differently
- Many Werkstudent roles require current enrollment (*Immatrikulationsbescheinigung*)

## Contributing

The most valuable PR: **add English-friendly companies** to
[`data/companies.yaml`](data/companies.yaml) — one line each, slug from the company's
careers URL (please verify the API responds before submitting). Also welcome: new
source adapters (`src/sources/`), better German-requirement patterns
(`src/filters/rules.py`), new notifiers (`src/notify/`).

## License

MIT
