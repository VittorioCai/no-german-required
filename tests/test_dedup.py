import unittest

from src.main import deduplicate_jobs
from src.sources.base import Job


class DedupTests(unittest.TestCase):
    def test_canonical_urls_ignore_tracking_and_trailing_slash(self):
        first = Job("a", "Intern", "Acme", "Berlin", "https://jobs.acme.com/1/?utm_source=board", "short", "arbeitnow")
        direct = Job("b", "Intern", "Acme", "Berlin", "https://jobs.acme.com/1", "long direct description", "personio")
        self.assertEqual(deduplicate_jobs([first, direct]), [direct])

    def test_signature_dedup_prefers_direct_source(self):
        aggregate = Job("a", "Data Intern (m/f/d)", "Acme GmbH", "Berlin", "https://board.example/a", "long aggregate description", "arbeitnow")
        direct = Job("b", " data intern m/f/d ", "ACME GMBH", "Berlin", "https://acme.example/b", "direct", "recruitee")
        self.assertEqual(deduplicate_jobs([aggregate, direct]), [direct])

    def test_distinct_jobs_remain(self):
        one = Job("a", "Data Intern", "Acme", "Berlin", "https://acme/1", "", "personio")
        two = Job("b", "Finance Intern", "Acme", "Berlin", "https://acme/2", "", "personio")
        self.assertEqual(deduplicate_jobs([one, two]), [one, two])

    def test_url_and_signature_bridge_merges_transitive_duplicates(self):
        by_url = Job("a", "Data Intern", "Acme", "Munich", "https://acme/shared", "one", "arbeitnow")
        by_signature = Job("b", "Data Intern", "Acme", "Berlin", "https://acme/other", "two", "personio")
        bridge = Job("c", "Data Intern", "Acme", "Berlin", "https://acme/shared", "best description", "recruitee")
        self.assertEqual(deduplicate_jobs([by_url, by_signature, bridge]), [bridge])


if __name__ == "__main__":
    unittest.main()
