import unittest
from datetime import datetime, timedelta, timezone

from job_availability import _hostname, next_status


class SafeAvailabilityTests(unittest.TestCase):
    def setUp(self):
        self.now = datetime(2026, 10, 12, 14, 0, tzinfo=timezone.utc)

    def test_rejects_untrusted_hosts_and_insecure_urls(self):
        self.assertIsNone(_hostname("http://portal.gupy.io/job/1"))
        self.assertIsNone(_hostname("https://portal.gupy.io.evil.example/job/1"))
        self.assertIsNone(_hostname("https://127.0.0.1/job"))
        self.assertEqual(_hostname("https://portal.gupy.io/job/1"), "portal.gupy.io")

    def test_one_404_never_closes_job(self):
        self.assertEqual(next_status(404, "portal.gupy.io", now=self.now), ("suspected_closed", 1))

    def test_two_separate_404_checks_can_close(self):
        previous = (self.now - timedelta(days=2)).isoformat()
        self.assertEqual(next_status(404, "portal.gupy.io", "suspected_closed", 1, previous, self.now), ("closed", 2))

    def test_second_check_same_day_does_not_close(self):
        previous = (self.now - timedelta(hours=3)).isoformat()
        self.assertEqual(next_status(404, "portal.gupy.io", "suspected_closed", 1, previous, self.now), ("suspected_closed", 1))

    def test_linkedin_404_and_bot_blocks_do_not_close(self):
        self.assertEqual(next_status(404, "br.linkedin.com", now=self.now), ("unverified", 0))
        self.assertEqual(next_status(403, "portal.gupy.io", now=self.now), ("unverified", 0))
        self.assertEqual(next_status(429, "portal.gupy.io", now=self.now), ("unverified", 0))

    def test_200_does_not_claim_confirmed_open(self):
        self.assertEqual(next_status(200, "portal.gupy.io", "suspected_closed", 1, now=self.now), ("unverified", 0))


if __name__ == "__main__":
    unittest.main()
