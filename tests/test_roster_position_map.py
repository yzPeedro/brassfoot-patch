import unittest
from tools.roster_position_map import (brasfoot_code, display_player_name, legacy_display_name, normalize,
                                       validate_source_url)


class PositionMappingTests(unittest.TestCase):
    def test_explicit_roles(self):
        self.assertEqual(brasfoot_code("Goleiro"), 0)
        self.assertEqual(brasfoot_code("Lateral Direito"), 1)
        self.assertEqual(brasfoot_code("Zagueiro Central"), 2)
        self.assertEqual(brasfoot_code("Volante"), 3)
        self.assertEqual(brasfoot_code("Meia Atacante"), 3)
        self.assertEqual(brasfoot_code("Ponta Esquerda"), 4)
        self.assertEqual(brasfoot_code("Centroavante"), 4)
        self.assertEqual(brasfoot_code("Centre Back"), 2)
        self.assertEqual(brasfoot_code("Defensive Midfield"), 3)

    def test_ambiguous_roles_rejected(self):
        for value in ["Defensor", "Defender", "Jogador", "Técnico", "", "Goleiro/Atacante"]:
            with self.subTest(value=value), self.assertRaises(ValueError):
                brasfoot_code(value)

    def test_reference_urls(self):
        self.assertEqual(validate_source_url("https://www.365scores.com/pt-br/football/team/cruzeiro-1213/squad"),
                         "https://www.365scores.com/pt-br/football/team/cruzeiro-1213/squad")
        self.assertEqual(validate_source_url("https://www.365scores.com/pt-br/football/team/maranhao-ma-12748/squad"),
                         "https://www.365scores.com/pt-br/football/team/maranhao-ma-12748/squad")
        for value in ["https://evil.example/squad", "http://www.365scores.com/football/team/a-1/squad",
                      "https://www.365scores.com/pt-br/football/team/a-1/squad?redirect=x"]:
            with self.subTest(value=value), self.assertRaises(ValueError):
                validate_source_url(value)


class DisplayNameTests(unittest.TestCase):
    def test_two_words_keep_particles_with_the_surname(self):
        cases = {"João Pedro Silva": "João Pedro", "Neymar": "Neymar", "Vinícius Júnior": "Vinícius Júnior",
                 "Matheus dos Santos Silva": "Matheus dos Santos", "David de Gea": "David de Gea",
                 "Jesús de la Fuente": "Jesús de la Fuente", "Ibrahim Al Ahbabi": "Ibrahim Al Ahbabi"}
        for full, shown in cases.items():
            self.assertEqual(display_player_name(full), shown)
        self.assertEqual(legacy_display_name("Matheus dos Santos Silva"), "Matheus dos")


if __name__ == "__main__":
    unittest.main()
