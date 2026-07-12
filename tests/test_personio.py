import unittest
from unittest.mock import Mock, patch

from src.sources.personio import PersonioSource


XML = b'''<?xml version="1.0" encoding="UTF-8"?>
<workzag-jobs><position><id>42</id><subcompany>Acme Labs</subcompany><office>Munich</office>
<name>Working Student Data</name><jobDescriptions>
<jobDescription><name>Mission</name><value>&lt;p&gt;Build &amp;amp; analyze data.&lt;/p&gt;</value></jobDescription>
</jobDescriptions></position></workzag-jobs>'''


class PersonioTests(unittest.TestCase):
    @patch("src.sources.personio.requests.get")
    def test_parses_public_xml_feed(self, get):
        get.return_value = Mock(content=XML)
        get.return_value.raise_for_status.return_value = None
        jobs = PersonioSource([{"name": "Acme", "ats": "personio", "slug": "acme"}]).fetch()
        self.assertEqual(len(jobs), 1)
        self.assertEqual(jobs[0].id, "personio:acme:42")
        self.assertEqual(jobs[0].location, "Munich")
        self.assertIn("Build & analyze data.", jobs[0].description)
        self.assertEqual(jobs[0].url, "https://acme.jobs.personio.de/job/42?language=en")

    @patch("src.sources.personio.requests.get", side_effect=RuntimeError("offline"))
    def test_company_failure_is_isolated(self, get):
        self.assertEqual(PersonioSource([{"name": "Acme", "ats": "personio", "slug": "acme"}]).fetch(), [])


if __name__ == "__main__":
    unittest.main()
