# Reliability Hardening Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Make LLM judgments, notifications, and scan persistence robust while correcting the documented German-language scoring behavior.

**Architecture:** Keep the current modules and standard-library-first dependency footprint. Validate at the LLM boundary, sanitize at notifier boundaries, and persist successful processing before external notification calls.

**Tech Stack:** Python 3.12, requests, PyYAML, unittest, GitHub Actions

---

### Task 1: Validate and Retry LLM Judgments

**Files:**
- Modify: `src/filters/llm_judge.py`
- Create: `tests/test_llm_judge.py`

- [ ] Write tests that patch `complete_json`, assert valid judgments pass unchanged, malformed structures retry once, and two invalid responses return an `LLM error:` judgment.
- [ ] Run `python -m unittest tests.test_llm_judge -v` and confirm failures because validation and retry do not exist.
- [ ] Add a focused `_validate_judgment` function with exact enums, string/list checks, a non-boolean numeric score in `[0, 100]`, and a two-attempt loop in `judge`.
- [ ] Re-run the focused tests and confirm they pass.

### Task 2: Escape Notification Content and Reject Unsafe Links

**Files:**
- Modify: `src/notify/email.py`
- Modify: `src/notify/telegram.py`
- Create: `tests/test_notifications.py`

- [ ] Write tests that render hostile text and `javascript:` URLs through each `_card`, asserting escaped visible content and no unsafe link attribute.
- [ ] Run `python -m unittest tests.test_notifications -v` and confirm the unsafe rendering failures.
- [ ] Add small text-escaping and HTTP(S)-URL helpers and apply them to every external value in both cards.
- [ ] Re-run the focused tests and confirm they pass.

### Task 3: Persist Before Notification

**Files:**
- Modify: `src/main.py`
- Create: `tests/test_main.py`

- [ ] Write a pipeline test with fake sources, judgment, persistence, and a failing notifier; assert persistence occurs before the notification exception and the successful job ID is saved.
- [ ] Run `python -m unittest tests.test_main -v` and confirm it fails under the current ordering.
- [ ] Retain rejected IDs during the existing gate pass, save successful judgments and rejected IDs before notification, and remove the duplicate gate evaluation.
- [ ] Re-run the focused test and confirm it passes.

### Task 4: Correct Documentation and Add CI Tests

**Files:**
- Modify: `README.md`
- Modify: `README.zh-CN.md`
- Modify: `.github/workflows/daily.yml`
- Create: `tests/test_readme.py`

- [ ] Write a documentation test asserting both READMEs describe a 10-20 point deduction and do not claim a score cap at 30.
- [ ] Run `python -m unittest tests.test_readme -v` and confirm it fails on the current text.
- [ ] Correct both READMEs and add `python -m unittest discover -s tests -v` before the pipeline step in the workflow.
- [ ] Run the full suite, `python -m compileall -q src tests`, and `git diff --check`; confirm all exit successfully.

### Task 5: Live Dry Run and Review

**Files:** None

- [ ] Run `python -m src.main --dry-run` against live public sources and record source failures separately from code failures.
- [ ] Inspect `git diff --stat`, `git diff`, and `git status --short` to ensure every change maps to the approved scope.
- [ ] Commit the implementation with a focused message after all verification passes.
