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

        self.assertTrue({"missoes", "competitivo", "reputacao", "ativos"}.issubset(valores))
        self.assertTrue(
            {f"jogo:{slug}" for slug in ranking_missoes_jogos.JOGOS}.issubset(valores)
        )
        self.assertEqual(
            next(opcao for opcao in seletor.options if opcao.value == "reputacao").default,
            True,
        )
        self.assertLessEqual(len(seletor.options), 25)

    def test_ranking_por_jogo_tem_opcao_individual_para_cada_jogo_cadastrado(self):
        guild = SimpleNamespace(id=1563995879981981817)
        view = RankingPublicoView(None, guild)
        seletor = next(item for item in view.children if hasattr(item, "options"))

        for slug, dados in ranking_missoes_jogos.JOGOS.items():
            opcao = next(item for item in seletor.options if item.value == f"jogo:{slug}")
            self.assertIn(dados["nome"], opcao.label)
            self.assertIn(dados["nome"], opcao.description)


if __name__ == "__main__":
    unittest.main()
