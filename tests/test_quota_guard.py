"""Offline SQLite quota concurrency and provider limit tests."""
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest
from unittest.mock import patch

from quota_guard import HARD_LIMIT, RESERVED, TARGET_LIMIT, QuotaExceeded, QuotaLedger


class PersistentQuotaTests(unittest.TestCase):
    def test_budget_is_conservative_and_persistent(self):
        with TemporaryDirectory() as directory:
            path = Path(directory) / "quota.sqlite3"
            quota = QuotaLedger(path, max_calls=3)
            self.assertEqual(quota.reserve("private-api-key", day="2026-10-25"), 1)
            self.assertEqual(QuotaLedger(path, max_calls=3).reserve("private-api-key", day="2026-10-25"), 2)
            self.assertEqual(quota.reserve("private-api-key", day="2026-10-25"), 3)
            with self.assertRaises(QuotaExceeded):
                quota.reserve("private-api-key", day="2026-10-25")
            self.assertEqual(quota.snapshot("private-api-key", day="2026-10-25")["localRequests"], 3)
            self.assertEqual(quota.reserve("private-api-key", day="2026-10-26"), 1)
            self.assertNotIn("private-api-key", path.read_bytes().decode("latin1"))

    def test_concurrent_callers_never_exceed_limit(self):
        with TemporaryDirectory() as directory:
            path = Path(directory) / "quota.sqlite3"
            def reserve(_):
                try:
                    QuotaLedger(path, max_calls=15).reserve("shared", day="2026-10-25")
                    return True
                except QuotaExceeded:
                    return False
            with ThreadPoolExecutor(max_workers=20) as pool:
                values = list(pool.map(reserve, range(100)))
            self.assertEqual(sum(values), 15)
            self.assertEqual(QuotaLedger(path, max_calls=15).snapshot("shared", day="2026-10-25")["localRequests"], 15)

    def test_provider_headers_never_expand_local_quota(self):
        with TemporaryDirectory() as directory:
            quota = QuotaLedger(Path(directory) / "q.sqlite3", max_calls=3)
            quota.record_headers("abc", {"x-ratelimit-requests-remaining": "999"}, day="2026-10-25")
            for _ in range(3):
                quota.reserve("abc", day="2026-10-25")
            with self.assertRaises(QuotaExceeded):
                quota.reserve("abc", day="2026-10-25")
            quota.record_headers("abc", {"x-ratelimit-requests-remaining": "5"}, day="2026-10-25")
            self.assertEqual(quota.snapshot("abc", day="2026-10-25")["providerRemainingLastObserved"], 5)
            with self.assertRaises(QuotaExceeded):
                quota.reserve("abc", day="2026-10-25")

    def test_no_utc_midnight_burst_even_when_day_counter_resets(self):
        # Conservative rolling 24h budget prevents 90 requests at 23:59
        # followed by another 90 at 00:01 without any provider reset proof.
        with TemporaryDirectory() as directory:
            quota = QuotaLedger(Path(directory) / "rolling.sqlite3", max_calls=3)
            with patch("quota_guard.time.time", return_value=1792972799):
                for _ in range(3):
                    quota.reserve("same-api-key")
            with patch("quota_guard.time.time", return_value=1792972801):
                with self.assertRaises(QuotaExceeded):
                    quota.reserve("same-api-key")
            with patch("quota_guard.time.time", return_value=1793059200):
                quota.reserve("same-api-key")

    def test_90_plus_10_never_exceeds_100(self):
        self.assertEqual(HARD_LIMIT, 100)
        self.assertEqual(TARGET_LIMIT + RESERVED, HARD_LIMIT)
        with TemporaryDirectory() as directory:
            quota = QuotaLedger(Path(directory) / "q.sqlite3")
            for i in range(TARGET_LIMIT):
                self.assertEqual(quota.reserve("abc", day="2026-10-25"), i + 1)
            with self.assertRaises(QuotaExceeded):
                quota.reserve("abc", day="2026-10-25")
        with self.assertRaises(ValueError):
            QuotaLedger(Path("irrelevant.db"), max_calls=101)


if __name__ == "__main__":
    unittest.main()
