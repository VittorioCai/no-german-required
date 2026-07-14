# P1/P2 Improvements Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Complete state, prioritization, observability, confidence, CI, and open-source readiness improvements and push them to `main`.

**Architecture:** Extend existing modules with small deterministic helpers. Preserve legacy state reads, keep pre-scoring internal, validate confidence at the LLM boundary, and test each behavior with standard-library unittest.

**Tech Stack:** Python 3.12, unittest, GitHub Actions, GitHub CLI

---

### Task 1: Timestamped Seen State

**Files:** Modify `src/main.py`; modify `tests/test_main.py`

- [ ] Add failing tests proving legacy IDs load, timestamped records load, and saving retains the chronologically newest records.
- [ ] Run `python -m unittest tests.test_main -v` and confirm failures come from the old set format.
- [ ] Implement dictionary state, epoch migration, UTC timestamps, and chronological retention.
- [ ] Re-run the focused tests and confirm success.

### Task 2: Candidate Priority and Rejection Stats

**Files:** Modify `src/filters/rules.py`; modify `src/main.py`; create `tests/test_priority.py`; modify `tests/test_main.py`

- [ ] Add failing tests for the specified pre-score ordering and printed rejection counts.
- [ ] Run focused tests and confirm the helper/order does not yet exist.
- [ ] Implement `pre_score`, sort candidates before the LLM cap, and count gate reasons.
- [ ] Re-run focused tests and confirm success.

### Task 3: Language Confidence

**Files:** Modify `src/filters/llm_judge.py`; modify `src/notify/email.py`; modify `src/notify/telegram.py`; modify `tests/test_llm_judge.py`; modify `tests/test_notifications.py`

- [ ] Add failing tests for required confidence validation and percentage rendering.
- [ ] Run focused tests and confirm failures.
- [ ] Extend the prompt, validator, fallback result, and notification cards with confidence.
- [ ] Re-run focused tests and confirm success.

### Task 4: CI and Community Readiness

**Files:** Modify `.github/workflows/daily.yml`; modify `README.md`; modify `README.zh-CN.md`; create `CONTRIBUTING.md`; create `SECURITY.md`; modify `tests/test_readme.py`

- [ ] Add tests for workflow concurrency and corrected README/community claims.
- [ ] Run focused tests and confirm failures.
- [ ] Add concurrency, correct documentation, and create the two community files.
- [ ] Re-run focused tests and confirm success.

### Task 5: Verify and Publish

**Files:** All scoped files

- [ ] Run the full unittest suite, compileall, and diff check.
- [ ] Run `python -m src.main --dry-run` against live sources.
- [ ] Review the complete diff, commit, pull/rebase if required, and push `main`.
- [ ] Update repository description/topics and verify remote commit and Actions status.
