# Project Rebrand Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Rebrand and rename the project to English Job Agent for Germany without changing runtime behavior.

**Architecture:** Replace user-facing identity strings, protect them with a regression test, push the code first, then rename the GitHub repository and update the local remote.

**Tech Stack:** Python unittest, Git, GitHub CLI

---

### Task 1: Brand References

**Files:** Modify `tests/test_readme.py`, `README.md`, `README.zh-CN.md`, `src/main.py`, `src/notify/email.py`, `CONTRIBUTING.md`, `LICENSE`

- [ ] Add a test requiring the display name, tagline, and new email prefix while rejecting the old slug from active project files.
- [ ] Run the focused test and confirm it fails on the old identity.
- [ ] Replace all active identity references while retaining the approved tagline.
- [ ] Run the full suite, compile check, and diff check.

### Task 2: Publish and Rename

**Files:** No additional repository files

- [ ] Commit and push branding changes to the current `main`.
- [ ] Rename the GitHub repository to `english-job-agent-germany`.
- [ ] Update local `origin`, repository description, and verify the new URL, old redirect, remote commit, and clean worktree.
