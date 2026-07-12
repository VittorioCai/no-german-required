# Reliability Hardening Design

## Scope

This change hardens the existing daily scan without adding new product features or changing the project's lightweight architecture.

It covers four runtime risks and their regression tests:

1. Validate the LLM judgment structure and retry malformed output once.
2. Escape untrusted job and LLM text in email and Telegram notifications, and allow only HTTP(S) job links.
3. Persist successfully processed job IDs before attempting notification, so a notification outage does not repeat paid LLM calls.
4. Correct the English and Chinese README descriptions of the German-language penalty.

## Confirmed Language-Penalty Behavior

Jobs whose German requirement exceeds the user's level remain eligible. The LLM is instructed to subtract 10-20 points and add a clear red flag. Python does not impose a score cap, and the README must not claim that scores are capped at 30.

## LLM Validation

Keep dependencies minimal and implement validation in the existing LLM-judging boundary. A valid judgment must contain:

- `working_language`: `English`, `German`, or `unclear`
- `german_required`: `none`, `nice-to-have`, `B1-B2`, or `C1+`
- `evidence`: string
- `match_score`: numeric value from 0 through 100 (booleans are invalid)
- `red_flags`: list of strings
- `summary`: string

Malformed JSON and invalid structures trigger one additional LLM request. If both attempts fail, the existing failure judgment is returned with an `LLM error:` red flag, leaving the job eligible for retry on a future scan.

## Notification Safety

Email and Telegram render job-board data and model output as HTML. Every visible external value is escaped. Job URLs are accepted only when their scheme is `http` or `https`; unsafe or malformed URLs render as non-clickable text.

## Persistence and Failure Flow

After judgments are complete, compute and save the new `seen` set before calling notification providers. Only successful judgments and rule-rejected jobs are recorded. If email or Telegram raises an exception, the workflow still fails visibly, but already paid-for successful judgments are not repeated the next day.

The implementation will reuse the gate results collected during filtering instead of calling the gate a second time solely for persistence.

## Tests and CI

Use the standard-library `unittest` framework to avoid a new runtime dependency. Regression tests cover:

- valid and invalid LLM judgment fields
- retry after malformed output and failure after two attempts
- HTML escaping and unsafe-link handling in both notifiers
- state persistence occurring before a simulated notification failure
- README language matching the confirmed score-penalty behavior

GitHub Actions runs the unit tests before the daily pipeline. A test failure prevents scanning and state mutation.

## Out of Scope

- Deterministic German-level score caps
- Candidate pre-ranking
- Database or external state storage
- New job sources or notification providers
- General refactoring unrelated to these risks

## Acceptance Criteria

- Invalid LLM judgments cannot enter sorting or notification code.
- One malformed LLM response is retried exactly once.
- Notification HTML cannot be altered by unescaped job/model text.
- A notification exception occurs only after successful judgment state is saved.
- Both READMEs say that excessive German requirements cause a 10-20 point deduction and red flag, not a score cap.
- The complete unit-test suite passes in a clean checkout.
