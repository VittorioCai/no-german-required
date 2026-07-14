# Safe Subagents Recovery Design

## Goal

Restore the reliable `English Job Agent for Germany` pipeline from `4266e79`, then retain the two useful additions from `6a7445e` without reintroducing its state, security, cost, source-coverage, documentation, or testing regressions.

## Recovery boundary

The recovery restores the timestamped 2,763-entry seen state, all 45 configured company sources, cross-source deduplication, candidate pre-scoring, LLM response validation and retry, escaped notification rendering, save-before-notify ordering, workflow concurrency, the test suite, contribution/security documents, and the repository's current branding.

The only product additions retained from `6a7445e` are:

- cached company briefings for digest matches;
- a local CLI that drafts, but never sends, cover letters;
- local/public state files needed by those features and concise documentation.

## Company-intel component

Company intel is opt-in through `ENABLE_COMPANY_INTEL`; the default daily scan makes no extra intel calls. When enabled, `MAX_INTEL_CALLS` reserves part of the existing `MAX_LLM_CALLS` total budget, so judgment and intel calls cannot exceed that total.

The intel prompt labels the job posting as untrusted evidence and tells the model not to follow instructions inside it. Every response must be a JSON object containing string fields `what`, `scale`, and `language_culture`, plus one to three string `talking_points`. Invalid responses are retried only while budget remains and are never cached. Cache writes are atomic, cached records expire after `COMPANY_INTEL_TTL_DAYS`, and invalid or legacy cache entries are treated as misses.

All intel strings pass through the same HTML escaping used for job and judgment fields before appearing in email.

## Draft component

The cover-letter feature remains a manual command. It reads only validated jobs previously placed in `data/matches.json`, sends the selected job plus `cv_summary` to the configured LLM, and writes a local plain-text draft under the gitignored `drafts/` directory. It never submits an application or sends a message.

The prompt explicitly marks the posting as untrusted input. Draft filenames include a stable URL hash so jobs with identical company/title text do not overwrite each other. Existing files are not silently replaced.

## Pipeline and failure handling

The stable fetch, deduplication, gating, and priority behavior remains unchanged. Actual model attempts, including validation retries, share one call budget. After judgment, successfully processed and rule-rejected jobs are written atomically to `seen.json` before company intel, match persistence, or notifications. The workflow state-commit step uses `if: always()` so a later notifier failure can still persist completed paid work. A workflow concurrency group prevents scheduled and manual scans from racing, and checkout credentials are exposed only to the final state-push step.

`matches.json` contains at most 200 recent digest jobs and no applicant profile. `company_intel.json` contains only validated public-company summaries and timestamps. Neither file contains API keys.

## Verification

New tests cover total LLM budgeting, opt-in behavior, intel schema validation, retry/budget exhaustion, cache expiry and corruption, HTML escaping of intel, collision-safe draft paths, and save-before-notify behavior with intel enabled. The restored suite must pass, Python sources must compile, whitespace checks must pass, and a live dry-run must finish without LLM or notification calls.
