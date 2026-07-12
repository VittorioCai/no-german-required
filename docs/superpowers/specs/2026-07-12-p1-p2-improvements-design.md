# P1/P2 Improvements Design

## Scope

Complete the previously identified P1 and P2 work without introducing a database, web UI, or new runtime dependency. The change improves state retention, GitHub Actions safety, LLM-budget allocation, filter observability, language-confidence reporting, and open-source onboarding.

## State Retention and Compatibility

`data/seen.json` moves from a list of string IDs to timestamped records:

```json
{"seen": [{"id": "source:job", "seen_at": "2026-07-12T12:00:00+00:00"}]}
```

`load_seen()` returns an ID-to-timestamp dictionary. It accepts both the new records and legacy string entries. Legacy entries receive the Unix epoch timestamp during migration so genuinely new records are retained ahead of them when the 20,000-entry limit is reached. Invalid individual records are ignored; an invalid top-level document falls back to an empty state as it does today.

`save_seen()` sorts by timestamp and retains the most recent 20,000 records. New successful judgments and rule rejections receive the current UTC timestamp. Membership checks continue to use dictionary keys, including the Workday `skip_ids` path.

## Workflow Concurrency

The daily workflow receives one repository-wide concurrency group with `cancel-in-progress: false`. Scheduled and manual scans therefore queue instead of racing to push state commits.

## Candidate Pre-Scoring

Only jobs that pass the existing hard gate are pre-scored. The score is deterministic and used solely to choose which jobs consume the capped LLM budget; it does not appear in the digest and does not replace the LLM match score.

Signals:

- unique field-keyword matches: 10 points each, capped at 40
- unique role-keyword matches in the title: 5 points each, capped at 15
- an explicit English-friendly pattern: 20 points
- a hard German-requirement pattern when `apply_anyway` kept the job: minus 20 points
- description completeness: up to 10 points at 4,000 characters

Ties preserve source order. Candidate selection sorts descending by pre-score before applying `MAX_LLM_CALLS`.

## Rejection Observability

The gate pass retains its existing reason strings and counts them with `Counter`. Runtime output prints one stable, descending summary line per rejection reason. Dry runs include the same summary, so users can tune `profile.yaml` without paid calls.

## Language Confidence

The LLM contract adds `language_confidence`, a numeric value from 0 through 1 representing confidence in the working-language and German-requirement judgment. It does not modify `match_score`; it is displayed in email and Telegram as a percentage. The existing strict validator rejects missing, boolean, nonnumeric, or out-of-range values and retries once.

## Open-Source Readiness

Repository files gain:

- `CONTRIBUTING.md` with setup, tests, source-adapter guidance, and pull-request expectations
- `SECURITY.md` with private vulnerability-reporting guidance and supported-version policy
- README corrections for the real secret count, default Top 10, schedule behavior across German daylight-saving time, updated architecture wording, confidence output, tests, and contributing links

GitHub repository metadata is updated after the code push:

- description: concise international-student job-agent summary
- topics: `job-search`, `germany`, `international-students`, `github-actions`, `llm`, `python`

No release or tag is created in this change.

## Testing

Standard-library `unittest` coverage includes:

- legacy and timestamped state loading
- retention by timestamp rather than lexicographic ID
- deterministic candidate ordering and LLM budget selection
- rejection-reason counts
- confidence validation and notifier rendering
- workflow concurrency configuration
- README claims and presence of community documents

The full suite, compile check, diff check, and live `--dry-run` must pass before push. After pushing directly to `main`, verify the remote commit and GitHub Actions status.

## Out of Scope

- SQLite, external storage, or artifact-backed state
- changing gate acceptance/rejection behavior
- using the pre-score as the user-visible match score
- automatic applications
- release creation

## Acceptance Criteria

- Overlapping workflow runs cannot concurrently mutate repository state.
- The 20,000-entry retention policy keeps chronologically newest records.
- Legacy `seen.json` files migrate without reprocessing existing IDs.
- The LLM budget is spent on deterministically higher-priority candidates.
- Rejected-job reasons are visible in normal and dry-run output.
- Every accepted LLM judgment contains valid language confidence displayed in both notifiers.
- Repository onboarding claims match actual defaults and workflows.
- Tests and a live dry run pass before the verified `main` push.
