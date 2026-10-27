import unittest

from tools.release_traceability import TraceabilityError, validate_traceability


class ReleaseTraceabilityTest(unittest.TestCase):
    def setUp(self):
        self.manifest = {
            "publishedVersion": "2026.3.6",
            "commit": "ABC1234",
            "snapshot": "snapshot-2026-10-27",
            "sha256": "A" * 64,
        }

    def test_normalizes_and_returns_release_identity(self):
        self.assertEqual(validate_traceability(self.manifest), {
            "version": "2026.3.6",
            "commit": "abc1234",
            "snapshot": "snapshot-2026-10-27",
            "sha256": "a" * 64,
        })

    def test_rejects_missing_or_malformed_identity(self):
        for field, value in (("commit", ""), ("snapshot", " "), ("sha256", "bad")):
            candidate = dict(self.manifest, **{field: value})
            with self.subTest(field=field), self.assertRaises(TraceabilityError):
                validate_traceability(candidate)

    def test_rejects_wrong_release_version(self):
        with self.assertRaises(TraceabilityError):
            validate_traceability(dict(self.manifest, publishedVersion="v2026.3.6"))


if __name__ == "__main__":
    unittest.main()
