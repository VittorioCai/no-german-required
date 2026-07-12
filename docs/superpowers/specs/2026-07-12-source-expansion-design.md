# Source Expansion Design

## Scope

Add cross-source deduplication and three public career-feed adapters: Personio XML, SmartRecruiters Posting API, and Recruitee Careers Site API. Seed only endpoints verified live on 2026-07-12. Do not scrape login-protected job boards or add credentials.

## Cross-Source Deduplication

Normalize HTTP(S) URLs by lowercasing the host, removing fragments, common tracking parameters, and trailing slashes. Also build a normalized signature from company, title, and location. Jobs match when either a nonempty canonical URL or the full signature matches.

When duplicates match, retain the higher-quality record: a direct company ATS beats the Arbeitnow aggregator, then the longer description wins. Output raw and unique counts before the existing seen/application dedup stage. Digest `total` represents unique jobs; `fetched` retains the raw count for diagnostics.

## Personio

Add `src/sources/personio.py`. Fetch `https://{slug}.jobs.personio.de/xml?language=en`, parse response bytes as XML, combine all `jobDescription/value` sections, strip embedded HTML, and produce a stable `personio:{slug}:{id}` ID. Build the application URL as `https://{slug}.jobs.personio.de/job/{id}?language=en`. One failed company is logged and skipped.

Initial verified companies:

- UnternehmerTUM (`unternehmertum`)
- TWAICE (`twaice`)
- Entrix (`entrix`)
- Start2 Group (`start2`)

## SmartRecruiters

Add `src/sources/smartrecruiters.py`. Page through the public company postings endpoint with `country=de`. Filter list results to student-role title stems (`werkstud`, `working student`, `intern`, `praktik`, `thesis`, `student assistant`) before requesting details, with a maximum of 40 detail requests per company. Combine all job-ad sections, use `postingUrl`, and emit stable IDs. One failed company or detail is logged and skipped without stopping other companies.

Initial verified companies:

- Scalable Capital (`ScalableGmbH`)
- Seven Senders (`SevenSenders`)
- Haufe Group (`HaufeGroup`)

Bosch is intentionally excluded from the first release because its board currently exposes roughly 950 postings and needs separate performance evaluation.

## Recruitee

Add `src/sources/recruitee.py`. Fetch `https://{slug}.recruitee.com/api/offers/`, select the English translation when present, combine description and requirements, normalize location fields, and use careers URLs with stable `recruitee:{slug}:{id}` IDs. One failed company is logged and skipped.

Initial verified companies:

- neXenio (`nexenio`)
- Trafineo (`trafineo`)
- Dance (`dance`)

## Pipeline and Configuration

Instantiate the three new sources alongside existing direct ATS and Workday sources. Fetch direct company sources before Arbeitnow so ties naturally favor first-party data, while the quality comparator remains the final authority. Extend `data/companies.yaml` comments and entries without changing existing entries.

Update both READMEs with the new source families and current company count. Add source-level unit tests with mocked HTTP responses, deduplication tests, full-suite verification, and a live dry run. The dry run must not modify state or call the LLM.

## Acceptance Criteria

- Duplicate jobs consume at most one gate and LLM slot per run.
- Legacy and new sources continue after individual company failures.
- All new source records contain stable IDs, readable text, locations, and application URLs.
- SmartRecruiters request volume is bounded.
- The full test suite, compile check, diff check, and live dry run pass before pushing `main`.
