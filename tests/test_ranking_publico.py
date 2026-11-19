import unittest
from types import SimpleNamespace

from cogs.missoes import RankingPublicoView
from utils import ranking_missoes_jogos


class TestRankingPublico(unittest.TestCase):
    def test_seletor_reune_rankings_gerais_atividade_e_jogos(self):
        guild = SimpleNamespace(id=1563995879981981817)
        view = RankingPublicoView(None, guild, selecionado="reputacao")
        seletor = next(item for item in view.children if hasattr(item, "options"))
        valores = {opcao.value for opcao in seletor.options}

        self.assertEqual(valores, {"reputacao", "jogos", "ativos"})
        self.assertFalse({"missoes", "competitivo"}.intersection(valores))
        self.assertFalse(any(valor.startswith("jogo:") for valor in valores))
        self.assertEqual(
            next(opcao for opcao in seletor.options if opcao.value == "reputacao").default,
            True,
        )
        self.assertLessEqual(len(seletor.options), 25)


if __name__ == "__main__":
    unittest.main()
