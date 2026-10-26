import unittest
from tools.roster_position_map import brasfoot_code, normalize, validate_source_url


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


if __name__ == "__main__":
    unittest.main()
