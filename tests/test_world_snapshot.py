import json
import tempfile
import unittest
from pathlib import Path

from tools.world_snapshot import create_snapshot, diff_snapshots, load_snapshot


class WorldSnapshotTests(unittest.TestCase):
    def setUp(self):
        self.record = {"type": "club", "id": "club-1", "fields": {"name": "Synthetic FC", "division": "A"},
                       "provenance": {"source_url": "https://example.invalid/club-1", "effective_at": "2026-01-01"}}
        self.first = create_snapshot({"fixture": {"status": "ok", "records": [self.record]}}, observed_at="clock-1")

    def test_identical_content_has_stable_hash_and_no_new_version(self):
        later = create_snapshot({"fixture": {"status": "ok", "records": [self.record]}}, self.first, observed_at="clock-2")
        self.assertEqual(later["content_hash"], self.first["content_hash"])
        self.assertEqual(later["content_version"], self.first["content_version"])
        self.assertNotEqual(later["observed_at"], self.first["observed_at"])
        self.assertFalse(later["diff"]["content_changed"])

    def test_changed_field_creates_content_version_and_diff(self):
        changed = {**self.record, "fields": {**self.record["fields"], "division": "B"}}
        result = create_snapshot({"fixture": {"status": "ok", "records": [changed]}}, self.first)
        self.assertEqual(result["content_version"], self.first["content_version"] + 1)
        self.assertEqual(diff_snapshots(self.first, result)["changes"], [
            {"entity": "club/club-1", "field": "division", "before": "A", "after": "B"}
        ])

    def test_failed_empty_or_missing_source_preserves_trusted_fields(self):
        for outcomes in (
            {"fixture": {"status": "failed", "error": "offline", "records": []}},
            {"fixture": {"status": "ok", "records": []}},
            {},
        ):
            result = create_snapshot(outcomes, self.first, observed_at="later")
            self.assertEqual(result["content"]["entities"], self.first["content"]["entities"])
            self.assertEqual(result["content_hash"], self.first["content_hash"])
            self.assertEqual(result["content_version"], self.first["content_version"])
        failed = create_snapshot({"fixture": {"status": "failed", "error": "offline"}}, self.first)
        self.assertEqual(failed["source_status"]["fixture"]["status"], "failed")

    def test_crash_before_atomic_replace_keeps_previous_file(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "snapshot.json"
            create_snapshot({"fixture": {"status": "ok", "records": [self.record]}}, path=path)
            previous_bytes = path.read_bytes()
            changed = {**self.record, "fields": {**self.record["fields"], "division": "B"}}

            def crash(_temporary):
                raise RuntimeError("simulated interruption")

            with self.assertRaisesRegex(RuntimeError, "simulated interruption"):
                create_snapshot({"fixture": {"status": "ok", "records": [changed]}},
                                load_snapshot(path), path=path, before_replace=crash)
            self.assertEqual(path.read_bytes(), previous_bytes)
            self.assertEqual(load_snapshot(path)["content"]["entities"], self.first["content"]["entities"])

    def test_conflicting_source_value_is_retained_for_reconciliation(self):
        disagreement = {"type": "club", "id": "club-1", "fields": {"name": "Different FC"}}
        result = create_snapshot({"second-source": {"status": "ok", "records": [disagreement]}}, self.first)
        entity = result["content"]["entities"]["club/club-1"]
        self.assertEqual(entity["fields"]["name"]["value"], "Synthetic FC")
        self.assertEqual(len(result["content"]["conflicts"]), 1)
        self.assertEqual(result["content"]["conflicts"][0]["field"], "name")

    def test_dry_run_does_not_write(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "snapshot.json"
            result = create_snapshot({"fixture": {"status": "ok", "records": [self.record]}}, path=path, dry_run=True)
            self.assertFalse(path.exists())
            self.assertTrue(result["content_hash"])


if __name__ == "__main__":
    unittest.main()
