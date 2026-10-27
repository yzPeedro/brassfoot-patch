import unittest

from tools.history_records import HistoryLedger, Record


class HistoryRecordsTests(unittest.TestCase):
    def test_historical_requires_provenance_but_simulated_does_not(self):
        with self.assertRaises(ValueError):
            Record("wc", "historical", "competition", "Completed Cup", "2022-12-18").validate()
        ledger = HistoryLedger()
        ledger.add(Record("sim-1", "simulated", "award", "Manager of the Year", "2026-12-31"))
        self.assertIn("sim-1", ledger.export())

    def test_duplicate_ids_are_rejected(self):
        ledger = HistoryLedger()
        record = Record("a", "current", "award", "Live award", "2026-01-01")
        ledger.add(record)
        with self.assertRaises(ValueError):
            ledger.add(record)

    def test_export_is_deterministic_and_sorted(self):
        ledger = HistoryLedger()
        ledger.add(Record("b", "current", "award", "B", "2026-01-01"))
        ledger.add(Record("a", "historical", "competition", "A", "2022-12-18", "https://example.test/source", "high"))
        self.assertEqual(ledger.export(), ledger.export())
        self.assertLess(ledger.export().index('"id": "a"'), ledger.export().index('"id": "b"'))

    def test_round_trip_preserves_separation(self):
        ledger = HistoryLedger()
        ledger.add(Record("h", "historical", "award", "Award", "2022-12-18", "https://example.test/source", "high"))
        ledger.add(Record("s", "simulated", "award", "Award", "2026-12-31"))
        loaded = HistoryLedger.from_json(ledger.export())
        self.assertEqual(loaded.export(), ledger.export())


if __name__ == "__main__":
    unittest.main()
