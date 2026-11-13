import base64
import contextlib
import hashlib
import io
import json
import os
import sys
import tempfile
import unittest
from pathlib import Path

from tools import regression_suite as rs

FULL, SEASON, LIVE, ORIGINAL = "f" * 64, "5" * 64, "1" * 64, "0" * 64
OLD_FULL = "9" * 64


def h(text: str) -> str:
    return hashlib.sha256(text.encode()).hexdigest()


def manifest(version="2026.9.1"):
    return {
        "version": version,
        "files": [
            {"path": "bf22-23.exe", "operation": "replace", "sha256": FULL, "size": 10,
             "acceptedOriginalSha256": [ORIGINAL, OLD_FULL, LIVE], "vanillaSha256": ORIGINAL},
            {"path": "conf_ligas_nacionais/BRA.cfg", "component": "season", "operation": "replace", "sha256": h("bra-new"),
             "vanillaSha256": h("bra-old")},
            {"path": "conf_ligas_nacionais/ARG.cfg", "component": "rosters", "operation": "add", "sha256": h("arg"),
             "vanillaMissing": True},
            {"path": "teams/a_bra.ban", "component": "rosters", "operation": "replace", "sha256": h("a-new"),
             "vanillaSha256": h("a-old")},
            {"path": "teams/novo_arg.ban", "component": "rosters", "operation": "add", "sha256": h("novo"),
             "vanillaMissing": True},
            {"path": "teams/escudos/a_bra.png", "component": "crests", "operation": "replace", "sha256": h("crest-new"),
             "vanillaSha256": h("crest-old"), "recipe": "crest-1.json"},
            {"path": "teams/camisas/novo_arg.png", "component": "crests", "operation": "add", "sha256": h("shirt"),
             "vanillaMissing": True, "recipe": "crest-2.json"},
        ],
        "components": {
            "originalExecutableSha256": ORIGINAL,
            "liveExecutableSha256": [LIVE, FULL],
            "liveOnlyExecutableSha256": [],
            "executables": {"patch+live": {"sha256": FULL}, "patch": {"sha256": SEASON, "acceptedOriginalSha256": [ORIGINAL, OLD_FULL]},
                            "live": {"sha256": LIVE, "acceptedOriginalSha256": [ORIGINAL, FULL, SEASON]}},
            "variants": {"full": {"sha256": FULL}, "season": {"sha256": SEASON}, "live": {"sha256": LIVE},
                         "original": {"sha256": ORIGINAL}},
        },
    }


def section(status):
    return {"status": status}


class VerdictTests(unittest.TestCase):
    def test_pass_only_when_every_section_passes(self):
        sections = {name: section(rs.PASS) for name in rs.SECTIONS}
        self.assertEqual(rs.build_verdict(sections), rs.PASS)
        self.assertEqual(rs.exit_code_for(rs.build_verdict(sections)), 0)

    def test_any_failure_fails_even_with_skips(self):
        sections = {name: section(rs.PASS) for name in rs.SECTIONS}
        sections["matrix"] = section(rs.SKIP)
        sections["site"] = section(rs.FAIL)
        self.assertEqual(rs.build_verdict(sections), rs.FAIL)
        self.assertEqual(rs.exit_code_for(rs.FAIL), 1)

    def test_skipped_or_missing_section_is_incomplete_and_not_zero(self):
        sections = {name: section(rs.PASS) for name in rs.SECTIONS if name != "render"}
        verdict = rs.build_verdict(sections)
        self.assertEqual(verdict, "incomplete")
        self.assertEqual(rs.exit_code_for(verdict), 1)

    def test_section_status_requires_evidence_and_no_failures(self):
        self.assertEqual(rs.section_status([], []), rs.FAIL)
        self.assertEqual(rs.section_status([rs.check("a", True)], [{"status": rs.PASS}]), rs.PASS)
        self.assertEqual(rs.section_status([rs.check("a", True)], [{"status": rs.FAIL}]), rs.FAIL)
        self.assertEqual(rs.section_status([rs.check("a", False)], []), rs.FAIL)

    def test_selected_sections_keep_canonical_order_and_reject_unknown(self):
        self.assertEqual(rs.selected_sections("site,suites"), ["suites", "site"])
        self.assertEqual(rs.selected_sections(None), list(rs.SECTIONS))
        with self.assertRaises(SystemExit):
            rs.selected_sections("suites,gameplay")


class ExpectationTests(unittest.TestCase):
    def test_full_install_expects_every_manifest_hash(self):
        m = manifest()
        expected = rs.expected_state(m, set(rs.COMPONENTS))
        self.assertEqual(expected, {entry["path"]: entry["sha256"] for entry in m["files"]})

    def test_removal_returns_vanilla_hash_and_deletes_vanilla_missing(self):
        m = manifest()
        expected = rs.expected_state(m, {"season", "live", "crests"})
        self.assertEqual(expected["teams/a_bra.ban"], h("a-old"))
        self.assertIsNone(expected["teams/novo_arg.ban"])
        self.assertIsNone(expected["conf_ligas_nacionais/ARG.cfg"])
        self.assertEqual(expected["conf_ligas_nacionais/BRA.cfg"], h("bra-new"))
        self.assertEqual(expected["bf22-23.exe"], FULL)
        self.assertEqual(rs.expected_state(m, {"live", "crests"})["bf22-23.exe"], LIVE)
        self.assertEqual(rs.expected_state(m, {"season"})["bf22-23.exe"], SEASON)
        empty = rs.expected_state(m, set())
        self.assertEqual(empty["bf22-23.exe"], ORIGINAL)
        self.assertEqual(empty["teams/escudos/a_bra.png"], h("crest-old"))
        self.assertIsNone(empty["teams/camisas/novo_arg.png"])

    def test_component_of_crest_follows_path_even_without_field(self):
        self.assertEqual(rs.file_component({"path": "teams/escudosMini/x_bra.png"}), "crests")
        self.assertEqual(rs.file_component({"path": "conf_ligas_nacionais/BRA.cfg"}), "season")
        self.assertEqual(rs.file_component({"path": "teams/x_bra.ban"}), "rosters")

    def test_origin_flags_mirror_hub_detection(self):
        m = manifest()
        self.assertEqual(rs.origin_flags(m, ORIGINAL), (False, False))
        self.assertEqual(rs.origin_flags(m, FULL), (True, True))
        self.assertEqual(rs.origin_flags(m, LIVE), (False, True))
        self.assertEqual(rs.origin_flags(m, SEASON), (True, False))
        self.assertEqual(rs.origin_flags(m, OLD_FULL), (True, False))
        self.assertEqual(rs.origin_flags(m, "a" * 64), (False, False))
        self.assertEqual(rs.origin_flags(m, None), (False, False))

    def test_only_patch_keeps_crests_and_follows_live_of_origin(self):
        m = manifest()
        origin = {"bf22-23.exe": LIVE, "teams/escudos/a_bra.png": h("custom"), "teams/a_bra.ban": h("a-old")}
        expected = rs.only_expectation(m, "patch", origin)
        self.assertEqual(expected["bf22-23.exe"], FULL)
        self.assertEqual(expected["teams/a_bra.ban"], h("a-new"))
        self.assertEqual(expected["teams/escudos/a_bra.png"], h("custom"))
        self.assertIsNone(expected["teams/camisas/novo_arg.png"])
        vanilla = rs.only_expectation(m, "patch", {"bf22-23.exe": ORIGINAL})
        self.assertEqual(vanilla["bf22-23.exe"], SEASON)

    def test_only_live_keeps_files_and_follows_patch_of_origin(self):
        m = manifest()
        origin = {"bf22-23.exe": ORIGINAL, "teams/a_bra.ban": h("a-old")}
        expected = rs.only_expectation(m, "live", origin)
        self.assertEqual(expected["bf22-23.exe"], LIVE)
        self.assertEqual(expected["teams/a_bra.ban"], h("a-old"))
        self.assertIsNone(expected["teams/novo_arg.ban"])
        self.assertEqual(rs.only_expectation(m, "live", {"bf22-23.exe": SEASON})["bf22-23.exe"], FULL)

    def test_state_problems_report_absence_and_truncate(self):
        problems = rs.state_problems({"a": "1", "b": None, "c": "3"}, {"a": "1", "b": "2", "c": None})
        self.assertEqual(len(problems), 2)
        self.assertIn("b: esperado ausente, encontrado 2", problems)
        many = rs.state_problems({str(i): "x" for i in range(30)}, {}, limit=5)
        self.assertEqual(len(many), 6)
        self.assertIn("mais 25", many[-1])

    def test_tree_helpers_detect_changes_and_absent_sav(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self.assertEqual(rs.tree_digest(root / "sav"), "ausente")
            (root / "sav").mkdir()
            (root / "sav" / "info.txt").write_text("a")
            first = rs.tree_digest(root / "sav")
            before = rs.tree_hashes(root)
            (root / "sav" / "info.txt").write_text("b")
            self.assertNotEqual(first, rs.tree_digest(root / "sav"))
            self.assertEqual(len(rs.tree_problems(before, rs.tree_hashes(root))), 1)
            state = rs.read_state(root, ["sav/info.txt", "sav/missing"])
            self.assertIsNone(state["sav/missing"])


class BundleTests(unittest.TestCase):
    def test_zip_may_only_hold_manifest_and_recipes(self):
        good = ["bundled_release/", "bundled_release/manifest.json", "bundled_release/patches/a.ban.json"]
        self.assertEqual(rs.zip_content_errors(good), [])
        bad = rs.zip_content_errors(["bundled_release/manifest.json", "bundled_release/patches/bf22-23.exe",
                                     "teams/a.ban", "bundled_release/patches/sub/x.json"])
        self.assertEqual(len(bad), 3)
        self.assertTrue(rs.zip_content_errors(["bundled_release/patches/a.json"]))

    def step(self, origin, target, size, literal):
        operations = [{"copy": [0, size - literal]}] if size > literal else []
        if literal:
            operations.append({"add": base64.b64encode(b"x" * literal).decode()})
        return {"schemaVersion": 1, "path": "bf22-23.exe", "originalSha256": origin, "targetSha256": target,
                "originalSize": size, "targetSize": size, "operations": operations}

    def test_executable_literal_limit_and_chain_length(self):
        ok = {"schemaVersion": 2, "path": "bf22-23.exe", "variants": [self.step("a", "b", 100, 30)]}
        self.assertEqual(rs.recipe_errors("ok", ok), [])
        heavy = {"schemaVersion": 2, "path": "bf22-23.exe", "variants": [self.step("a", "b", 100, 31)]}
        self.assertTrue(rs.recipe_errors("heavy", heavy))
        chain = {"schemaVersion": 3, "steps": [self.step(str(i), str(i + 1), 100, 1) for i in range(9)]}
        long = {"schemaVersion": 2, "path": "bf22-23.exe", "variants": [chain]}
        self.assertIn("9 passos", rs.recipe_errors("long", long)[0])
        broken = {"schemaVersion": 3, "steps": [self.step("a", "b", 100, 1), self.step("c", "d", 100, 1)]}
        self.assertIn("descontínua", rs.recipe_errors("broken", {"schemaVersion": 2, "path": "bf22-23.exe", "variants": [broken]})[0])

    def test_team_recipe_is_not_bound_by_executable_literal_limit(self):
        team = {"schemaVersion": 2, "path": "teams/a.ban", "variants": [dict(self.step("a", "b", 10, 10), path="teams/a.ban")]}
        self.assertEqual(rs.recipe_errors("team", team), [])

    def test_inheritance_flags_missing_and_changed_entries(self):
        previous = manifest()
        self.assertTrue(all(item["ok"] for item in rs.inheritance_report(previous, manifest()).values()))
        candidate = manifest()
        candidate["files"] = [entry for entry in candidate["files"] if entry["path"] != "teams/camisas/novo_arg.png"]
        for entry in candidate["files"]:
            if entry["path"] == "teams/novo_arg.ban":
                entry["sha256"] = h("outro")
        report = rs.inheritance_report(previous, candidate)
        self.assertFalse(report["escudosECamisas"]["ok"])
        self.assertEqual(report["escudosECamisas"]["missing"], ["teams/camisas/novo_arg.png"])
        self.assertFalse(report["clubesSuperUpdate"]["ok"])
        self.assertEqual(report["clubesSuperUpdate"]["changed"], ["teams/novo_arg.ban"])
        self.assertTrue(report["ligas"]["ok"])
        relaxed = rs.inheritance_report(previous, candidate, super_update_recompiled=True)
        self.assertTrue(relaxed["clubesSuperUpdate"]["ok"])
        self.assertFalse(relaxed["escudosECamisas"]["ok"])

    def test_brazilian_replacements_are_not_inheritance_entries(self):
        categories = rs.inheritance_categories(manifest())
        self.assertEqual(set(categories["ligas"]), {"conf_ligas_nacionais/ARG.cfg"})
        self.assertEqual(set(categories["clubesSuperUpdate"]), {"teams/novo_arg.ban"})
        self.assertEqual(len(categories["escudosECamisas"]), 2)

    def test_requires_hub_rules(self):
        self.assertEqual(rs.requires_hub_errors({"version": "1.4.2", "requiresHub": "1.4.0"}, None, {}), [])
        self.assertTrue(rs.requires_hub_errors({"version": "1.4.2", "requiresHub": "1.3.9"}, None, {}))
        self.assertTrue(rs.requires_hub_errors({"version": "1.3.0", "requiresHub": "1.4.0"}, None, {}))
        self.assertTrue(rs.requires_hub_errors({"version": "1.4.2", "requiresHub": "1.4.0"}, {"requiresHub": "1.2.0"}, {}))
        self.assertTrue(rs.requires_hub_errors({"version": "1.4.2", "requiresHub": "1.4.0"}, None, {"requiresHub": "1.5.0"}))
        self.assertTrue(rs.requires_hub_errors({"version": "x", "requiresHub": "1.4.0"}, None, {}))


class SavesAndSiteTests(unittest.TestCase):
    def test_identical_executables_pass_by_construction(self):
        checks = rs.executable_report(manifest(), manifest(), {"full": FULL, "season": SEASON, "live": LIVE}, ORIGINAL)
        self.assertTrue(all(item["status"] == rs.PASS for item in checks))

    def test_changed_executable_fails(self):
        candidate = manifest()
        candidate["components"]["variants"]["live"]["sha256"] = "2" * 64
        checks = rs.executable_report(candidate, manifest(), {"full": None, "season": None, "live": None}, ORIGINAL)
        failed = [item["name"] for item in checks if item["status"] == rs.FAIL]
        self.assertEqual(failed, ["variante live igual à release anterior"])
        checks = rs.executable_report(manifest(), manifest(), {"full": FULL, "season": SEASON, "live": LIVE}, "3" * 64)
        self.assertEqual([item["name"] for item in checks if item["status"] == rs.FAIL], ["variante original igual ao jogo limpo"])

    def test_site_versions_must_all_match(self):
        self.assertEqual(rs.site_version_errors({"a": "2026.6.7", "b": "2026.6.7"}), [])
        self.assertTrue(rs.site_version_errors({"a": "2026.6.7", "b": "2026.6.8"}))
        self.assertTrue(rs.site_version_errors({"a": None, "b": None}))

    def test_compiled_ban_hashes_against_manifest_and_vanilla(self):
        m = manifest()
        compiled = {"a_bra.ban": h("a-new"), "novo_arg.ban": h("novo"), "intocado_bra.ban": h("same")}
        vanilla = {"a_bra.ban": h("a-old"), "intocado_bra.ban": h("same")}
        self.assertEqual(rs.compiled_ban_errors(compiled, m, vanilla), [])
        self.assertEqual(len(rs.compiled_ban_errors(dict(compiled, **{"a_bra.ban": h("x")}), m, vanilla)), 1)
        drifted = dict(compiled, **{"intocado_bra.ban": h("changed")})
        self.assertIn("ausente do manifesto", rs.compiled_ban_errors(drifted, m, vanilla)[0])
        missing = {key: value for key, value in compiled.items() if key != "novo_arg.ban"}
        self.assertIn("ausente da compilação", rs.compiled_ban_errors(missing, m, vanilla)[0])
        stray = dict(compiled, **{"fantasma_bra.ban": h("f")})
        self.assertIn("fora do manifesto", rs.compiled_ban_errors(stray, m, vanilla)[0])


class ToolingTests(unittest.TestCase):
    def test_vet_accepts_only_known_windows_warning(self):
        accepted, other = rs.vet_findings("# brasfoot\n./hub_windows.go:638:28: possible misuse of unsafe.Pointer\n")
        self.assertEqual((len(accepted), other), (1, []))
        accepted, other = rs.vet_findings("# x\nhub_windows.go:640:3: possible misuse of unsafe.Pointer\nengine.go:9:2: unreachable code\n")
        self.assertEqual(accepted, [])
        self.assertEqual(len(other), 2)

    def test_last_json_reads_final_object(self):
        self.assertEqual(rs.last_json('Pacote local\n{"payloadVersion":"1"}\n'), {"payloadVersion": "1"})
        self.assertEqual(rs.last_json("sem json"), {})

    def test_version_tuple(self):
        self.assertEqual(rs.version_tuple("v1.4.0"), (1, 4, 0))
        self.assertGreater(rs.version_tuple("1.10.0"), rs.version_tuple("1.9.9"))
        with self.assertRaises(ValueError):
            rs.version_tuple("1.4.x")

    def test_state_fingerprint_detects_creation_and_change(self):
        with tempfile.TemporaryDirectory() as tmp:
            target = Path(tmp) / rs.STATE_DIR_NAME
            before = rs.state_fingerprint(target)
            self.assertFalse(before["exists"])
            target.mkdir()
            created = rs.state_fingerprint(target)
            self.assertNotEqual(before, created)
            self.assertIn("criado", rs.fingerprint_changes(before, created))
            (target / "live-match-debug.log").write_text("x")
            changed = rs.fingerprint_changes(created, rs.state_fingerprint(target))
            self.assertIn("live-match-debug.log criado", changed)
            self.assertIn("sem alteração", rs.fingerprint_changes(created, created))
            self.assertEqual(rs.state_fingerprint(None), {"path": None, "exists": False})

    def test_runner_records_exit_code_log_and_timeout(self):
        with tempfile.TemporaryDirectory() as tmp:
            runner = rs.Runner(Path(tmp) / "logs", dict(os.environ))
            ok = runner.run("t", "ok", [sys.executable, "-c", "print('ola')"], Path(tmp))
            self.assertEqual((ok["status"], ok["exitCode"]), (rs.PASS, 0))
            self.assertIn("ola", Path(ok["log"]).read_text(encoding="utf-8"))
            bad = runner.run("t", "bad", [sys.executable, "-c", "raise SystemExit(3)"], Path(tmp))
            self.assertEqual((bad["status"], bad["exitCode"]), (rs.FAIL, 3))
            allowed = runner.run("t", "any", [sys.executable, "-c", "raise SystemExit(3)"], Path(tmp), expect_exit=None)
            self.assertEqual(allowed["status"], rs.PASS)
            slow = runner.run("t", "slow", [sys.executable, "-c", "import time; time.sleep(5)"], Path(tmp), timeout=0.5)
            self.assertEqual((slow["status"], slow["exitCode"]), (rs.FAIL, None))
            self.assertNotIn("output", rs.public(ok))

    def test_work_directory_must_be_new_and_away_from_vanilla(self):
        with tempfile.TemporaryDirectory() as tmp:
            vanilla = Path(tmp) / "vanilla"
            vanilla.mkdir()
            (vanilla / "bf22-23.exe").write_bytes(b"exe")
            work = Path(tmp) / "work"
            args = rs.parse_args(["--work", str(work), "--vanilla", str(vanilla)])
            self.assertEqual(rs.validate_paths(rs.Context(args)), [])
            work.mkdir()
            (work / "x").write_text("x")
            self.assertTrue(rs.validate_paths(rs.Context(args)))
            inside = rs.parse_args(["--work", str(vanilla / "w"), "--vanilla", str(vanilla)])
            self.assertTrue(rs.validate_paths(rs.Context(inside)))

    def test_section_without_inputs_fails_instead_of_passing(self):
        with tempfile.TemporaryDirectory() as tmp:
            args = rs.parse_args(["--work", str(Path(tmp) / "w"), "--jdk", ""])
            ctx = rs.Context(args)
            for name in ("bundle", "saves", "site", "matrix", "ban"):
                result = rs.run_section(ctx, name)
                self.assertEqual(result["status"], rs.FAIL, name)

    def test_verdict_document_is_written_with_skips_and_no_gameplay_claim(self):
        with tempfile.TemporaryDirectory() as tmp:
            work = Path(tmp) / "w"
            with contextlib.redirect_stdout(io.StringIO()):
                code = rs.main(["--work", str(work), "--only", "bundle", "--jdk", ""])
            self.assertEqual(code, 1)
            document = json.loads((work / "verdict.json").read_text(encoding="utf-8"))
            self.assertEqual(document["verdict"], rs.FAIL)
            self.assertEqual(document["sections"]["matrix"]["status"], rs.SKIP)
            self.assertIs(document["gameplayVerified"], False)
            self.assertEqual(list(document["sections"]), list(rs.SECTIONS))


if __name__ == "__main__":
    unittest.main()
