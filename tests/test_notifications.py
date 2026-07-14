import unittest

from src.notify import email, telegram
from src.sources.base import Job


class NotificationTests(unittest.TestCase):
    def setUp(self):
        self.job = Job("id", "<b>Intern</b>", "A&B", "Berlin <HQ>", "javascript:alert(1)", "", "test")
        self.result = {
            "match_score": 70,
            "working_language": "English<script>",
            "german_required": "none",
            "evidence": "<img src=x>",
            "red_flags": ["<danger>"],
            "summary": "Great & safe",
            "language_confidence": 0.87,
        }

    def test_email_card_escapes_text_and_rejects_unsafe_url(self):
        card = email._card(self.job, self.result)
        self.assertNotIn("javascript:", card)
        self.assertNotIn("<script>", card)
        self.assertNotIn("<img src=x>", card)
        self.assertIn("&lt;b&gt;Intern&lt;/b&gt;", card)
        self.assertIn("87%", card)

    def test_telegram_card_escapes_text_and_rejects_unsafe_url(self):
        card = telegram._card(self.job, self.result)
        self.assertNotIn("javascript:", card)
        self.assertNotIn("<script>", card)
        self.assertIn("&lt;b&gt;Intern&lt;/b&gt;", card)
        self.assertIn("87%", card)

    def test_telegram_card_escapes_quotes_in_safe_scheme_url(self):
        self.job.url = 'https://example.com/" onclick="alert(1)'
        card = telegram._card(self.job, self.result)
        self.assertNotIn('onclick="alert(1)', card)
        self.assertIn("&quot;", card)

    def test_email_card_escapes_company_intel(self):
        self.result["intel"] = {
            "what": "<img src=x>",
            "scale": "Scale & growth",
            "language_culture": "<script>alert(1)</script>",
            "talking_points": ["<danger>", "Proof & impact"],
        }
        card = email._card(self.job, self.result)
        self.assertNotIn("<img src=x>", card)
        self.assertNotIn("<script>", card)
        self.assertIn("&lt;img src=x&gt;", card)
        self.assertIn("Scale &amp; growth", card)
        self.assertIn("Proof &amp; impact", card)


if __name__ == "__main__":
    unittest.main()
