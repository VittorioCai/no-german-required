# Safe Subagents Recovery Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Restore the stable pipeline and reintroduce company-intel and cover-letter helpers with bounded cost, validated output, safe rendering, and regression coverage.

**Architecture:** Revert the unsafe sync as a unit, preserving the known-good runtime and historical state. Add two focused modules under `src/agents/`; daily intel is opt-in and shares the existing total LLM budget, while drafting stays a manual local CLI. The pipeline persists paid progress before optional enrichment and notification.

**Tech Stack:** Python 3.12, `unittest`, YAML/JSON state, requests-based LLM client, GitHub Actions.

---

### Task 1: Restore the stable baseline

**Files:**
- Restore: runtime, sources, tests, docs, workflow, and `data/seen.json` changed by `6a7445e`
- Preserve for later reimplementation: `.gitignore` intent for `drafts/`

- [ ] **Step 1: Revert the unsafe sync**

Run: `git revert --no-edit 6a7445e`

Expected: the tree matches `4266e79` except for this design and plan; `data/seen.json` contains 2,763 timestamped entries.

- [ ] **Step 2: Verify the restored suite**

Run: `python -m unittest discover -s tests -v`

Expected: all 28 restored tests pass.

### Task 2: Specify total-budget and opt-in behavior

**Files:**
- Modify: `tests/test_main.py`
- Modify: `src/main.py`

- [ ] **Step 1: Write failing budget tests**

Add tests asserting `_llm_budgets(25, False, 3) == (25, 0)`, `_llm_budgets(25, True, 3) == (22, 3)`, and clamping when the intel request exceeds the total.

- [ ] **Step 2: Verify RED**

Run: `python -m unittest tests.test_main.MainTests.test_llm_budgets -v`

Expected: FAIL because `_llm_budgets` does not exist.

- [ ] **Step 3: Add the minimal helper**

Implement:

```python
def _llm_budgets(total: int, intel_enabled: bool, intel_max: int) -> tuple[int, int]:
    intel = min(max(intel_max, 0), max(total, 0)) if intel_enabled else 0
    return max(total - intel, 0), intel
```

Use its judgment limit in the existing candidate slice. Keep intel disabled unless `ENABLE_COMPANY_INTEL` is truthy.

- [ ] **Step 4: Verify GREEN**

Run: `python -m unittest tests.test_main -v`

Expected: all main tests pass.

### Task 3: Add validated, budgeted company intel

**Files:**
- Create: `src/agents/__init__.py`
- Create: `src/agents/intel.py`
- Create: `tests/test_agents.py`
- Create: `data/company_intel.json`

- [ ] **Step 1: Write failing validation and budget tests**

Test that valid intel is attached and cached; arrays, missing fields, non-string values, and non-list talking points are rejected; invalid cache entries are misses; expired entries are refreshed; and total `complete_json` calls never exceed `max_calls` including retries.

- [ ] **Step 2: Verify RED**

Run: `python -m unittest tests.test_agents.IntelTests -v`

Expected: import failure because `src.agents.intel` does not exist.

- [ ] **Step 3: Implement the minimal intel API**

Create `enrich(pairs, max_calls, ttl_days=30) -> int`. It loads the cache once, validates cached and fresh values with `_validate_briefing`, retries fresh responses only while calls remain, mutates each judgment with `judgment["intel"]`, writes validated records as `{company: {"updated_at": ..., "intel": ...}}`, and saves via a temporary file plus `os.replace`.

- [ ] **Step 4: Verify GREEN**

Run: `python -m unittest tests.test_agents.IntelTests -v`

Expected: all intel tests pass.

### Task 4: Safely integrate match persistence and drafting

**Files:**
- Modify: `src/main.py`
- Create: `src/agents/draft.py`
- Modify: `tests/test_agents.py`
- Create: `data/matches.json`
- Modify: `.gitignore`

- [ ] **Step 1: Write failing persistence and filename tests**

Test that match state is capped at 200 records, stores no profile data, and `_draft_path` produces different filenames for different URLs with the same company/title. Test that an existing draft path is rejected instead of overwritten.

- [ ] **Step 2: Verify RED**

Run: `python -m unittest tests.test_agents.DraftTests -v`

Expected: FAIL because the draft module and match persistence API do not exist.

- [ ] **Step 3: Implement minimal persistence and CLI**

Add `save_matches(top + near)` after seen-state persistence. Implement `python -m src.agents.draft --list` and URL-based drafting, with an untrusted-posting delimiter in the prompt and a filename ending in the first eight hex characters of `sha256(url)`; open output with exclusive mode `"x"`.

- [ ] **Step 4: Verify GREEN**

Run: `python -m unittest tests.test_agents.DraftTests -v`

Expected: all draft tests pass.

### Task 5: Preserve notification safety with intel fields

**Files:**
- Modify: `src/notify/email.py`
- Modify: `tests/test_notifications.py`

- [ ] **Step 1: Write the failing hostile-intel test**

Extend the judgment with intel containing `<img>`, `<script>`, ampersands, and hostile talking points. Assert none appears as raw markup and all visible content is escaped.

- [ ] **Step 2: Verify RED**

Run: `python -m unittest tests.test_notifications.NotificationTests.test_email_card_escapes_intel -v`

Expected: FAIL because the stable renderer does not yet render intel.

- [ ] **Step 3: Add escaped intel rendering**

Render the optional block using `html.escape(str(value))` for every scalar and talking point. Retain the existing HTTP(S)-only URL handling and language-confidence rendering.

- [ ] **Step 4: Verify GREEN**

Run: `python -m unittest tests.test_notifications -v`

Expected: all notification tests pass.

### Task 6: Restore CI guarantees and document the opt-in features

**Files:**
- Modify: `.github/workflows/daily.yml`
- Modify: `README.md`
- Modify: `README.zh-CN.md`
- Modify: `tests/test_readme.py`

- [ ] **Step 1: Write failing documentation/workflow assertions**

Assert the README describes a 10-20 point German penalty rather than a score cap, names `ENABLE_COMPANY_INTEL` and `MAX_INTEL_CALLS`, and states drafts are manual. Assert the workflow runs tests, has the concurrency group, passes the two intel variables, persists both new JSON files, and uses `if: always()` on state persistence.

- [ ] **Step 2: Verify RED**

Run: `python -m unittest tests.test_readme -v`

Expected: FAIL for missing subagent configuration/documentation.

- [ ] **Step 3: Update workflow and docs**

Keep restored branding and source counts. Add the opt-in intel settings, manual draft commands, privacy note, total-budget explanation, `if: always()`, and state-file persistence.

- [ ] **Step 4: Verify GREEN**

Run: `python -m unittest tests.test_readme -v`

Expected: all README/workflow tests pass.

### Task 7: Full verification and publication

**Files:**
- Verify all modified files

- [ ] **Step 1: Run the full suite**

Run: `python -m unittest discover -s tests -v`

Expected: all tests pass with zero failures and errors.

- [ ] **Step 2: Run static verification**

Run: `python -m compileall -q src tests`

Run: `git diff --check`

Expected: both exit 0.

- [ ] **Step 3: Run live no-cost verification**

Run: `python -u -m src.main --dry-run`

Expected: source fetching finishes, restored seen state avoids the historical Workday detail backlog, and no LLM or notifier is invoked.

- [ ] **Step 4: Inspect, commit, and push**

Run: `git diff --stat 4266e79..HEAD`, inspect the final diff, commit the feature changes, and push `main` only after all preceding checks pass.
