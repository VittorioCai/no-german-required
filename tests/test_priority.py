import unittest

from src.filters.rules import pre_score
from src.sources.base import Job


PROFILE = {"role_keywords": ["intern"], "field_keywords": ["data", "analytics"], "apply_anyway": True}


class PriorityTests(unittest.TestCase):
    def test_pre_score_rewards_field_and_english_signals(self):
        strong = Job("1", "Data Intern", "A", "Berlin", "https://a", "Data analytics. Company language is English. " + "x" * 4000, "test")
        weak = Job("2", "Intern", "B", "Berlin", "https://b", "data", "test")
        self.assertGreater(pre_score(strong, PROFILE), pre_score(weak, PROFILE))

    def test_pre_score_penalizes_hard_german_requirement(self):
        friendly = Job("1", "Data Intern", "A", "Berlin", "https://a", "data", "test")
        german = Job("2", "Data Intern", "B", "Berlin", "https://b", "data; fluent German required", "test")
        self.assertGreater(pre_score(friendly, PROFILE), pre_score(german, PROFILE))


if __name__ == "__main__":
    unittest.main()
