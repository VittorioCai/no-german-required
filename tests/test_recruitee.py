import unittest
from unittest.mock import Mock, patch

from src.sources.recruitee import RecruiteeSource


class RecruiteeTests(unittest.TestCase):
    @patch("src.sources.recruitee.requests.get")
    def test_prefers_english_translation_and_normalizes_location(self, get):
        offer = {"id": 7, "title": "Werkstudent Daten", "description": "Deutsch",
                 "requirements": "Deutsch", "careers_url": "https://acme.recruitee.com/o/data",
                 "locations": [{"city": "Berlin", "country_code": "DE"}],
                 "translations": {"en": {"title": "Working Student Data",
                                             "description": "<p>Analyze data</p>",
                                             "requirements": "<p>English</p>"}}}
        get.return_value = Mock()
        get.return_value.raise_for_status.return_value = None
        get.return_value.json.return_value = {"offers": [offer]}
        jobs = RecruiteeSource([{"name": "Acme", "ats": "recruitee", "slug": "acme"}]).fetch()
        self.assertEqual(jobs[0].title, "Working Student Data")
        self.assertEqual(jobs[0].location, "Berlin, DE")
        self.assertEqual(jobs[0].description, "Analyze data English")
        self.assertEqual(jobs[0].country, "DE")

    @patch("src.sources.recruitee.requests.get", side_effect=RuntimeError("offline"))
    def test_company_failure_is_isolated(self, get):
        self.assertEqual(RecruiteeSource([{"name": "Acme", "ats": "recruitee", "slug": "acme"}]).fetch(), [])


if __name__ == "__main__":
    unittest.main()
