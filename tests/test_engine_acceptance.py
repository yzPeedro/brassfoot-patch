import unittest

from tools.engine_acceptance import EvidenceError, validate_evidence


def evidence(**overrides):
    value = {
        "schemaVersion": 1,
        "synthetic": False,
        "platform": "windows",
        "testedCommit": "abc123",
        "testedBuildSha256": "a" * 64,
        "saveHashesUnchanged": True,
        "checks": {
            "gameplay": True,
            "calendar": True,
            "save_roundtrip": True,
            "rollback": True,
        },
    }
    value.update(overrides)
    return value


class EngineAcceptanceTest(unittest.TestCase):
    def test_accepts_only_complete_real_windows_evidence(self):
        result = validate_evidence(evidence())
        self.assertTrue(result["accepted"])
        self.assertEqual(result["checks"], ["gameplay", "calendar", "save_roundtrip", "rollback"])

    def test_rejects_synthetic_evidence(self):
        with self.assertRaises(EvidenceError):
            validate_evidence(evidence(synthetic=True))

    def test_rejects_missing_gameplay_and_save_proof(self):
        value = evidence(saveHashesUnchanged=False)
        value["checks"]["gameplay"] = False
        with self.assertRaises(EvidenceError) as error:
            validate_evidence(value)
        self.assertIn("gameplay", str(error.exception))

    def test_rejects_unvalidated_platform_or_build_identity(self):
        with self.assertRaises(EvidenceError):
            validate_evidence(evidence(platform="linux"))
        with self.assertRaises(EvidenceError):
            validate_evidence(evidence(testedBuildSha256=""))


if __name__ == "__main__":
    unittest.main()
