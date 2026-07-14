import os
import json
from contextlib import redirect_stdout
from datetime import datetime, timedelta, timezone
from io import StringIO
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from src import main
from src.sources.base import Job


JOB = Job("source:1", "Data Intern", "Example", "Berlin", "https://example.com/job", "data", "test", country="DE")
JUDGMENT = {
    "working_language": "English", "german_required": "none", "evidence": "English",
    "match_score": 80, "red_flags": [], "summary": "Good fit",
    "language_confidence": 0.9,
}


class Source:
    def __init__(self, *args, **kwargs):
        pass

    def fetch(self):
        return [JOB]


class EmptySource(Source):
    def fetch(self):
        return []


class MainTests(unittest.TestCase):
    def test_llm_budgets_reserve_intel_within_total_cap(self):
        self.assertEqual(main._llm_budgets(25, False, 3), (25, 0))
        self.assertEqual(main._llm_budgets(25, True, 3), (22, 3))
        self.assertEqual(main._llm_budgets(2, True, 5), (1, 1))
        self.assertEqual(main._llm_budgets(1, True, 5), (1, 0))
        self.assertEqual(main._llm_budgets(-1, True, 3), (0, 0))

    def test_judgment_retries_stay_within_actual_call_budget(self):
        jobs = [Job(f"job:{index}", "Data Intern", f"Company {index}", "Berlin",
                    f"https://example.com/{index}", "data", "test", country="DE")
                for index in range(4)]
        source = type("MultipleSource", (Source,), {"fetch": lambda self: jobs})
        profile = {"min_score": 30, "role_keywords": ["intern"], "field_keywords": ["data"]}
        with patch.object(main, "load_yaml", side_effect=[profile, {"companies": []}]), \
             patch.object(main, "load_seen", return_value={}), \
             patch("src.track.tracked_urls", return_value=set()), \
             patch.object(main, "ArbeitnowSource", source), \
             patch.object(main, "ATSSource", EmptySource), \
             patch("src.sources.workday.WorkdaySource", EmptySource), \
             patch.object(main, "gate", return_value=("pass", "ok")), \
             patch("src.filters.llm_judge.complete_json", return_value={"match_score": "bad"}) as complete, \
             patch.object(main, "save_seen"), patch.object(main, "save_matches"), \
             patch.object(main, "MAX_LLM_CALLS", 3), patch.object(main, "MAX_INTEL_CALLS", 0), \
             patch.dict(os.environ, {"ENABLE_COMPANY_INTEL": "false"}):
            main.run()

        self.assertEqual(complete.call_count, 3)

    def test_load_seen_accepts_legacy_and_timestamped_records(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "seen.json"
            path.write_text(json.dumps({"seen": ["legacy:1", {"id": "new:1", "seen_at": "2026-07-12T00:00:00+00:00"}]}))
            with patch.object(main, "SEEN_PATH", str(path)):
                seen = main.load_seen()
        self.assertEqual(set(seen), {"legacy:1", "new:1"})
        self.assertEqual(seen["legacy:1"], "1970-01-01T00:00:00+00:00")

    def test_save_seen_retains_chronologically_newest_records(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "seen.json"
            start = datetime(2026, 1, 1, tzinfo=timezone.utc)
            records = {f"id:{i:05d}": (start + timedelta(seconds=i)).isoformat()
                       for i in range(20001)}
            records["lexically-last-but-old"] = "1970-01-01T00:00:00+00:00"
            with patch.object(main, "SEEN_PATH", str(path)):
                main.save_seen(records)
            saved = json.loads(path.read_text())["seen"]
        ids = {record["id"] for record in saved}
        self.assertEqual(len(saved), 20000)
        self.assertNotIn("lexically-last-but-old", ids)

    def test_save_seen_uses_atomic_replace(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "seen.json"
            real_replace = os.replace
            with patch.object(main, "SEEN_PATH", str(path)), \
                 patch.object(main.os, "replace", wraps=real_replace) as replace:
                main.save_seen({"id": "2026-07-14T00:00:00+00:00"})
            replace.assert_called_once_with(f"{path}.tmp", str(path))
            self.assertEqual(json.loads(path.read_text())["seen"][0]["id"], "id")

    def test_successful_judgment_is_saved_before_notification_failure(self):
        events = []

        def save_seen(seen):
            events.append(("save", set(seen)))

        def fail_notification(*args):
            events.append(("notify", None))
            raise RuntimeError("SMTP unavailable")

        profile = {"min_score": 30}
        companies = {"companies": []}
        with patch.object(main, "load_yaml", side_effect=[profile, companies]), \
             patch.object(main, "load_seen", return_value={}), \
             patch("src.track.tracked_urls", return_value=set()), \
             patch.object(main, "ArbeitnowSource", Source), \
             patch.object(main, "ATSSource", Source), \
             patch("src.sources.workday.WorkdaySource", Source), \
             patch.object(main, "gate", return_value=("pass", "ok")), \
             patch("src.filters.llm_judge.judge_with_usage", return_value=(JUDGMENT, 1)), \
             patch.object(main, "save_seen", side_effect=save_seen), \
             patch.object(main, "save_matches"), \
             patch("src.notify.email.send_digest", side_effect=fail_notification), \
             patch.dict(os.environ, {"NOTIFY": "email"}):
            with self.assertRaisesRegex(RuntimeError, "SMTP unavailable"):
                main.run()

        self.assertEqual(set(events[0][1]), {JOB.id})
        self.assertEqual(events[1][0], "notify")

    def test_opt_in_intel_runs_after_state_save_and_before_notification(self):
        events = []

        def save_seen(seen):
            events.append(("save", set(seen)))

        def enrich(pairs, max_calls, ttl_days):
            events.append(("intel", max_calls, ttl_days, len(pairs)))
            return 1

        def save_matches(pairs):
            events.append(("matches", len(pairs)))

        def notify(*args):
            events.append(("notify", None))

        profile = {"min_score": 30}
        companies = {"companies": []}
        with patch.object(main, "load_yaml", side_effect=[profile, companies]), \
             patch.object(main, "load_seen", return_value={}), \
             patch("src.track.tracked_urls", return_value=set()), \
             patch.object(main, "ArbeitnowSource", Source), \
             patch.object(main, "ATSSource", Source), \
             patch("src.sources.workday.WorkdaySource", Source), \
             patch.object(main, "gate", return_value=("pass", "ok")), \
             patch("src.filters.llm_judge.judge_with_usage", return_value=(JUDGMENT.copy(), 1)), \
             patch.object(main, "save_seen", side_effect=save_seen), \
             patch.object(main, "save_matches", side_effect=save_matches), \
             patch("src.agents.intel.enrich", side_effect=enrich), \
             patch("src.notify.email.send_digest", side_effect=notify), \
             patch.object(main, "MAX_LLM_CALLS", 2), \
             patch.object(main, "MAX_INTEL_CALLS", 1), \
             patch.dict(os.environ, {"ENABLE_COMPANY_INTEL": "true", "NOTIFY": "email"}):
            main.run()

        self.assertEqual(events[0], ("save", {JOB.id}))
        self.assertEqual(events[1], ("matches", 1))
        self.assertEqual(events[2], ("intel", 1, 30, 1))
        self.assertEqual(events[3][0], "notify")

    def test_pipeline_prioritizes_candidates_and_reports_rejection_reasons(self):
        weak = Job("weak", "Data Intern", "A", "Berlin", "https://a", "data", "test", country="DE")
        strong = Job("strong", "Data Analytics Intern", "B", "Berlin", "https://b",
                     "data analytics; company language is English", "test", country="DE")
        rejected = Job("rejected", "Manager", "C", "Berlin", "https://c", "data", "test", country="DE")
        source = type("CandidateSource", (Source,), {"fetch": lambda self: [weak, strong, rejected]})
        judged_ids = []

        def judge(job, profile, max_calls):
            judged_ids.append(job.id)
            return {**JUDGMENT, "match_score": 0}, 1

        def gate(job, profile):
            return ("reject", "title does not match role keywords") if job.id == "rejected" else ("pass", "ok")

        profile = {"min_score": 30, "role_keywords": ["intern"],
                   "field_keywords": ["data", "analytics"]}
        output = StringIO()
        with patch.object(main, "load_yaml", side_effect=[profile, {"companies": []}]), \
             patch.object(main, "load_seen", return_value={}), \
             patch("src.track.tracked_urls", return_value=set()), \
             patch.object(main, "ArbeitnowSource", source), \
             patch.object(main, "ATSSource", EmptySource), \
             patch("src.sources.workday.WorkdaySource", EmptySource), \
             patch.object(main, "gate", side_effect=gate), \
             patch("src.filters.llm_judge.judge_with_usage", side_effect=judge), \
             patch.object(main, "save_seen"), patch.object(main, "save_matches"), \
             patch.object(main, "MAX_LLM_CALLS", 1), \
             redirect_stdout(output):
            main.run()

        self.assertEqual(judged_ids, ["strong"])
        self.assertIn("REJECT    1  title does not match role keywords", output.getvalue())


if __name__ == "__main__":
    unittest.main()
