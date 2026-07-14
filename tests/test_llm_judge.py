import unittest
from unittest.mock import patch

from src.filters.llm_judge import judge
from src.sources.base import Job


JOB = Job("id", "Intern Data", "Example", "Berlin", "https://example.com", "English team", "test")
PROFILE = {"german_level": "A1", "cv_summary": "Data student", "role_keywords": ["intern"], "field_keywords": ["data"]}
VALID = {
    "working_language": "English",
    "german_required": "none",
    "evidence": "English team",
    "match_score": 80,
    "red_flags": [],
    "summary": "Good fit",
    "language_confidence": 0.9,
}


class JudgeTests(unittest.TestCase):
    @patch("src.filters.llm_judge.complete_json", return_value=VALID.copy())
    def test_valid_judgment_is_returned_without_retry(self, complete):
        self.assertEqual(judge(JOB, PROFILE), VALID)
        complete.assert_called_once()

    @patch("src.filters.llm_judge.complete_json", side_effect=[{"match_score": "80"}, VALID.copy()])
    def test_invalid_structure_is_retried_once(self, complete):
        self.assertEqual(judge(JOB, PROFILE), VALID)
        self.assertEqual(complete.call_count, 2)

    @patch("src.filters.llm_judge.complete_json", side_effect=[{"match_score": True}, {"match_score": 101}])
    def test_two_invalid_structures_return_retryable_error(self, complete):
        result = judge(JOB, PROFILE)
        self.assertEqual(complete.call_count, 2)
        self.assertTrue(result["red_flags"][0].startswith("LLM error:"))

    @patch("src.filters.llm_judge.complete_json", side_effect=[{**VALID, "language_confidence": True}, {**VALID, "language_confidence": 1.1}])
    def test_invalid_language_confidence_is_retried_then_rejected(self, complete):
        result = judge(JOB, PROFILE)
        self.assertEqual(complete.call_count, 2)
        self.assertTrue(result["red_flags"][0].startswith("LLM error:"))


if __name__ == "__main__":
    unittest.main()
