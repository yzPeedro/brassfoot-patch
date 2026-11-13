import json
from pathlib import Path
import shutil
import unittest

from tools.daily_sources import collect_cached_sources, daily_snapshot


class DailySourcesTests(unittest.TestCase):
    def setUp(self):
        self.root = Path("data/private/daily-sources-test-fixture")
        shutil.rmtree(self.root, ignore_errors=True)
        self.root.mkdir(parents=True)
        self.addCleanup(lambda: shutil.rmtree(self.root, ignore_errors=True))
        (self.root / "feed.json").write_text(json.dumps([{
            "type": "club", "id": "br-1", "fields": {"name": "Clube"},
            "provenance": {"source_url": "https://example.invalid/source"},
        }]), encoding="utf-8")
        self.spec = [{"name": "cached", "path": "feed.json",
                      "source_url": "https://example.invalid/source"}]

    def test_reads_allowlisted_cache_without_network(self):
        result = collect_cached_sources(self.root, self.spec)
        self.assertEqual(result["cached"]["records"][0]["id"], "br-1")
        self.assertEqual(result["cached"]["provenance"]["sha256"].__len__(), 64)

    def test_requires_https_and_bounds_sources(self):
        result = collect_cached_sources(self.root, [{**self.spec[0], "source_url": "http://invalid"}])
        self.assertEqual(result["cached"]["status"], "failed")
        self.assertEqual(result["cached"]["records"], [])
        self.assertIn("HTTPS", result["cached"]["error"])
        self.assertNotIn("provenance", result["cached"])
        with self.assertRaisesRegex(ValueError, "bound"):
            collect_cached_sources(self.root, self.spec, max_sources=0)

    def test_daily_change_detection_is_offline_and_deterministic(self):
        first = daily_snapshot(self.root, self.spec, observed_at="2026-10-26T00:00:00Z")
        second = daily_snapshot(self.root, self.spec, previous=first["snapshot"],
                                observed_at="2026-10-27T00:00:00Z")
        self.assertEqual(second["network_requests"], 0)
        self.assertFalse(second["changes"]["changes"])
        self.assertFalse(second["snapshot"]["diff"]["content_changed"])

    def test_missing_cache_file_fails_closed(self):
        missing = [{**self.spec[0], "path": "missing.json"}]
        result = collect_cached_sources(self.root, missing)
        self.assertEqual(result["cached"]["status"], "failed")
        self.assertEqual(result["cached"]["records"], [])
        self.assertIn("missing.json", result["cached"]["error"])
        first = daily_snapshot(self.root, self.spec, observed_at="2026-10-26T00:00:00Z")
        second = daily_snapshot(self.root, missing, previous=first["snapshot"],
                                observed_at="2026-10-27T00:00:00Z")
        self.assertEqual(second["snapshot"]["content"]["entities"], first["snapshot"]["content"]["entities"])
        self.assertEqual(second["snapshot"]["content_hash"], first["snapshot"]["content_hash"])
        self.assertEqual(second["snapshot"]["source_status"]["cached"]["status"], "failed")


if __name__ == "__main__":
    unittest.main()
