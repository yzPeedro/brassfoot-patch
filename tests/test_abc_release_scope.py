"""A/B/C release scope gate: synthetic fixtures, no Brasfoot originals or network."""
import copy
import unittest

from tools.verify_abc_release_scope import ScopeError, verify_scope


def fixtures():
    catalog = {"season": 2026, "targetClubs": 60, "serieD": {"policy": "untouched"}, "clubs": []}
    mapping = {"season": 2026, "serieD": "ORIGINAL / NO CHANGES", "modifiesBRAcfg": False,
               "modifiesExistingSaves": False, "clubs": []}
    manifest = {"schemaVersion": 3, "patchSeason": 2026, "files": []}
    for division in "ABC":
        for i in range(20):
            maranhao = division == "C" and i == 19
            name = "Maranhão" if maranhao else f"Club {division}-{i}"
            state = "MA" if maranhao else "SP"
            club_id = f"club-{division}-{i}"
            path = "teams/maranhao_ma.ban" if maranhao else f"teams/club_{division}_{i}.ban"
            catalog["clubs"].append({"id": club_id, "name": name, "state": state, "division": division})
            source = f"{i + (ord(division) - 65) * 20 + 1:064x}"
            mapping["clubs"].append({
                "clubId": club_id, "club": name, "state": state, "division": division,
                "operation": "add_after_verified_creation" if maranhao else "replace_after_roster_validation",
                "originalTeamFile": None if maranhao else path,
                "newTeamFile": path if maranhao else None,
                "expectedSourceSHA256": None if maranhao else source,
            })
            manifest["files"].append({
                "path": path, "operation": "add" if maranhao else "replace",
                "sha256": f"{1000 + len(manifest['files']):064x}", "size": 2048,
                "acceptedOriginalSha256": [] if maranhao else [source],
            })
    return catalog, mapping, manifest


class ManifestScopeTests(unittest.TestCase):
    def setUp(self):
        self.target, self.mapping, self.manifest = fixtures()

    def test_passes_only_correct_declared_abc_scope(self):
        report = verify_scope(self.target, self.mapping, self.manifest)
        self.assertEqual((report["teamFiles"], report["replacements"], report["additions"]), (60, 59, 1))
        self.assertFalse(report["gameplayVerified"])
        self.assertFalse(report["readyForRelease"])

    def test_serie_d_or_shared_config_is_rejected(self):
        for malicious in ("conf_ligas_nacionais/BRA.cfg", "teams/serie_d.ban"):
            with self.subTest(malicious):
                forged = copy.deepcopy(self.manifest)
                forged["files"][0]["path"] = malicious
                with self.assertRaises(ScopeError):
                    verify_scope(self.target, self.mapping, forged)

    def test_missing_maranhao_target_must_fail_closed(self):
        self.mapping["clubs"][-1]["newTeamFile"] = None
        with self.assertRaisesRegex(ScopeError, "Unresolved"):
            verify_scope(self.target, self.mapping, self.manifest)

    def test_original_hash_is_required(self):
        self.manifest["files"][0]["acceptedOriginalSha256"] = ["0" * 64]
        with self.assertRaisesRegex(ScopeError, "Original hash"):
            verify_scope(self.target, self.mapping, self.manifest)

    def test_club_division_or_file_collision_is_rejected(self):
        self.mapping["clubs"][0]["division"] = "C"
        with self.assertRaises(ScopeError):
            verify_scope(self.target, self.mapping, self.manifest)
        _, mapping, manifest = fixtures()
        manifest["files"][1]["path"] = manifest["files"][0]["path"].replace("club_a_0", "CLUB_A_0")
        with self.assertRaisesRegex(ScopeError, "Duplicate"):
            verify_scope(self.target, mapping, manifest)

    def test_unverified_schema_and_missing_team_are_rejected(self):
        self.manifest["schemaVersion"] = 2
        with self.assertRaises(ScopeError):
            verify_scope(self.target, self.mapping, self.manifest)
        _, _, manifest = fixtures()
        manifest["files"].pop()
        with self.assertRaises(ScopeError):
            verify_scope(self.target, self.mapping, manifest)


if __name__ == "__main__":
    unittest.main()
