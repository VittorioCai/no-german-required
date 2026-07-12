import unittest
from unittest.mock import Mock, patch

from src.sources.smartrecruiters import SmartRecruitersSource


class SmartRecruitersTests(unittest.TestCase):
    @patch("src.sources.smartrecruiters.requests.get")
    def test_filters_titles_and_fetches_bounded_details(self, get):
        listing = {
            "totalFound": 2,
            "content": [
                {"id": "1", "name": "Working Student Data", "ref": "https://api/detail/1",
                 "location": {"country": "de", "fullLocation": "Berlin, Germany"}},
                {"id": "2", "name": "International Manager", "ref": "https://api/detail/2",
                 "location": {"country": "de", "fullLocation": "Munich, Germany"}},
            ],
        }
        detail = {"id": "1", "name": "Working Student Data",
                  "postingUrl": "https://jobs.smartrecruiters.com/Acme/1",
                  "location": {"fullLocation": "Berlin, Germany"},
                  "jobAd": {"sections": {"jobDescription": {"text": "<p>Analyze data</p>"},
                                            "qualifications": {"text": "<p>English</p>"}}}}

        def response(url, **kwargs):
            payload = detail if url == "https://api/detail/1" else listing
            result = Mock()
            result.raise_for_status.return_value = None
            result.json.return_value = payload
            return result

        get.side_effect = response
        jobs = SmartRecruitersSource([{"name": "Acme", "ats": "smartrecruiters", "slug": "Acme"}], max_details=2).fetch()
        self.assertEqual([job.id for job in jobs], ["smartrecruiters:Acme:1"])
        self.assertIn("Analyze data English", jobs[0].description)
        self.assertEqual(sum(call.args[0] == "https://api/detail/1" for call in get.call_args_list), 1)
        self.assertFalse(any(call.args[0] == "https://api/detail/2" for call in get.call_args_list))

    @patch("src.sources.smartrecruiters.requests.get")
    def test_listing_pagination_is_bounded(self, get):
        page = [{"id": str(index), "name": "Manager",
                 "location": {"country": "de"}} for index in range(100)]
        get.return_value = Mock()
        get.return_value.raise_for_status.return_value = None
        get.return_value.json.return_value = {"totalFound": 10000, "content": page}
        source = SmartRecruitersSource(
            [{"name": "Acme", "ats": "smartrecruiters", "slug": "Acme"}],
            max_postings=200,
        )
        self.assertEqual(source.fetch(), [])
        self.assertEqual(get.call_count, 2)

    @patch("src.sources.smartrecruiters.requests.get", side_effect=RuntimeError("offline"))
    def test_company_failure_is_isolated(self, get):
        self.assertEqual(SmartRecruitersSource([{"name": "Acme", "ats": "smartrecruiters", "slug": "Acme"}]).fetch(), [])


if __name__ == "__main__":
    unittest.main()
