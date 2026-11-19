import unittest
from datetime import date

from tools.manager_facts import coach_of, same_person, update

TODAY = date(2026, 11, 19)


def club(file, *staff, url="https://www.365scores.com/football/team/x-1/squad", when="2026-11-19T12:00:00+00:00"):
    return {"teamFile": file, "sourceUrl": url, "observedAt": when,
            "staff": [{"name": name, "role": role, "sourceId": n} for n, (name, role) in enumerate(staff)]}


class ManagerFactTests(unittest.TestCase):
    def test_single_coach_becomes_fact_with_source(self):
        ledger, report = update({"clubs": [club("teams/ajax_hol.ban", ("Míchel", "Coach"), ("Aux", "Assistant Coach"))]},
                                {"teams/ajax_hol.ban": "Alfred Schreuder"}, {"clubs": []}, TODAY)
        fact = ledger["clubs"][0]["fields"]["manager"]
        self.assertEqual(fact["value"], "Míchel")
        self.assertEqual(fact["sourceLevel"], "365scores-squad-staff")
        self.assertTrue(fact["sourceUrl"] and fact["sourcePublishedAt"])
        self.assertEqual(report["counts"], {"técnico novo": 1})

    def test_same_manager_is_not_a_fact(self):
        ledger, report = update({"clubs": [club("teams/a.ban", ("Abel Ferreira", "Coach"))]},
                                {"teams/a.ban": "Abel Ferreira"}, {"clubs": []}, TODAY)
        self.assertEqual(ledger["clubs"], [])
        self.assertEqual(report["counts"], {"igual ao publicado": 1})

    def test_ambiguous_or_missing_coach_is_skipped(self):
        observed = {"clubs": [club("teams/a.ban", ("Um", "Coach"), ("Dois", "Manager")), club("teams/b.ban")]}
        ledger, report = update(observed, {"teams/a.ban": "X", "teams/b.ban": "Y"}, {"clubs": []}, TODAY)
        self.assertEqual(ledger["clubs"], [])
        self.assertEqual(report["counts"], {"mais de um técnico na fonte": 1, "sem técnico na fonte": 1})

    def test_source_without_url_is_skipped(self):
        ledger, _ = update({"clubs": [club("teams/a.ban", ("Novo", "Coach"), url=None)]}, {"teams/a.ban": "Velho"},
                           {"clubs": []}, TODAY)
        self.assertEqual(ledger["clubs"], [])

    def test_other_identity_fields_are_kept_and_fact_date_is_stable(self):
        previous = {"clubs": [{"teamFile": "teams/a.ban", "fields": {
            "stadium": {"value": "Arena"}, "manager": {"value": "Novo", "recordedAt": "2026-11-01"}}}]}
        ledger, _ = update({"clubs": [club("teams/a.ban", ("Novo", "Coach"))]}, {"teams/a.ban": "Velho"}, previous, TODAY)
        fields = ledger["clubs"][0]["fields"]
        self.assertEqual(fields["stadium"], {"value": "Arena"})
        self.assertEqual(fields["manager"]["recordedAt"], "2026-11-01")

    def test_published_catching_up_drops_stale_fact(self):
        previous = {"clubs": [{"teamFile": "teams/a.ban", "fields": {"manager": {"value": "Interino"}}}]}
        ledger, _ = update({"clubs": [club("teams/a.ban", ("Efetivo", "Coach"))]}, {"teams/a.ban": "Efetivo"},
                           previous, TODAY)
        self.assertEqual(ledger["clubs"], [])

    def test_helpers(self):
        self.assertTrue(same_person("Rubén Albés", "Ruben Albes"))
        self.assertFalse(same_person("Rubi", "Francisco Pimienta"))
        self.assertTrue(same_person("Sergey Semak", "Sergei Semak"))
        self.assertFalse(same_person("Pedro Resende", "Pedro Silva"))
        self.assertEqual(coach_of({"staff": []})[2], "sem técnico na fonte")


if __name__ == "__main__":
    unittest.main()
