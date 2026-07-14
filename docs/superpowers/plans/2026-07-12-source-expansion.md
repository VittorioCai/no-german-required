# Source Expansion Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add cross-source deduplication and three bounded public ATS adapters.

**Architecture:** Keep each ATS in a focused source module, configure companies in YAML, and normalize duplicates once between fetch and seen filtering. Network tests use mocked responses; final verification uses live dry-run data.

**Tech Stack:** Python 3.12, requests, ElementTree, unittest

---

### Task 1: Cross-Source Deduplication

**Files:** Modify `src/main.py`; create `tests/test_dedup.py`; modify `tests/test_main.py`

- [ ] Add failing tests for canonical URL, signature matching, and direct-source preference.
- [ ] Run focused tests and confirm the helper is missing.
- [ ] Implement canonicalization, quality selection, stats, and pipeline integration.
- [ ] Re-run focused tests and confirm success.

### Task 2: Personio Adapter

**Files:** Create `src/sources/personio.py`; create `tests/test_personio.py`

- [ ] Add failing mocked XML parsing and company-failure tests.
- [ ] Implement the one-request XML adapter and run focused tests.

### Task 3: SmartRecruiters Adapter

**Files:** Create `src/sources/smartrecruiters.py`; create `tests/test_smartrecruiters.py`

- [ ] Add failing mocked pagination, title filtering, detail parsing, and request-limit tests.
- [ ] Implement the bounded list/detail adapter and run focused tests.

### Task 4: Recruitee Adapter

**Files:** Create `src/sources/recruitee.py`; create `tests/test_recruitee.py`

- [ ] Add failing mocked translation, location, description, and company-failure tests.
- [ ] Implement the one-request Careers Site adapter and run focused tests.

### Task 5: Integrate, Document, and Publish

**Files:** Modify `src/main.py`, `data/companies.yaml`, `README.md`, `README.zh-CN.md`, `tests/test_readme.py`

- [ ] Add failing configuration/documentation tests for all new ATS families.
- [ ] Integrate sources, add ten verified companies, and update both READMEs.
- [ ] Run the full suite, compile check, diff check, and live dry run.
- [ ] Review, commit, push `main`, and verify the remote commit.
