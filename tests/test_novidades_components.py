import unittest
from unittest.mock import AsyncMock, Mock, patch

import discord

from cogs.boas_vindas_dm import (
    AlternarAvisosButton,
    BoasVindasLayoutView,
    _reconstruir_cartao_preferencias,
)
from cogs.novidades import _enviar_dm_com_retry
from utils.apresentacao import (
    dividir_texto_components_v2,
    texto_embed_components_v2,
)


def _textos_do_container(container):
    return [
        item.content
        for item in container.children
        if isinstance(item, discord.ui.TextDisplay)
    ]


def _botoes_do_container(container):
    botoes = []
    for item in container.children:
        if isinstance(item, discord.ui.ActionRow):
            botoes.extend(
                filho for filho in item.children
                if isinstance(filho, discord.ui.Button)
            )
    return botoes


class TestTextoComponentsV2(unittest.TestCase):
    def test_divisao_preserva_todos_os_caracteres_e_respeita_limite(self):
        texto = ("linha importante\n" * 420) + ("x" * 4100)

        partes = dividir_texto_components_v2(texto)

        self.assertEqual("".join(partes), texto)
        self.assertTrue(partes)
        self.assertTrue(all(0 < len(parte) <= 3900 for parte in partes))

    def test_limite_invalido_e_rejeitado(self):
        for limite in (0, -1, 4001):
            with self.subTest(limite=limite):
                with self.assertRaises(ValueError):
                    dividir_texto_components_v2("conteúdo", limite)


class TestConversaoDeComunicados(unittest.IsolatedAsyncioTestCase):
    async def test_embed_legada_preserva_texto_imagens_e_cartao_v2(self):
        membro = Mock()
        membro.id = 123
        membro.send = AsyncMock()

        embed = discord.Embed(
            title="Comunicado importante",
            description=("Instrução completa.\n" * 260),
            url="https://example.com/comunicado",
            color=0x8B1E2D,
        )
        embed.set_author(name="NÊMESIS", url="https://example.com")
        embed.add_field(name="Detalhes", value="D" * 1024, inline=False)
        embed.set_thumbnail(url="https://example.com/miniatura.png")
        embed.set_image(url="https://example.com/banner.png")
        embed.set_footer(text="Nêmesis Systeam")

        resultado = await _enviar_dm_com_retry(membro, embed=embed)

        self.assertEqual(resultado, "enviada")
        membro.send.assert_awaited_once()
        view = membro.send.await_args.kwargs["view"]
        self.assertIsInstance(view, discord.ui.LayoutView)
        self.assertNotIn("embed", membro.send.await_args.kwargs)

        container = view.children[0]
        self.assertIsInstance(container, discord.ui.Container)
        textos = _textos_do_container(container)
        self.assertEqual("".join(textos), texto_embed_components_v2(embed))
        self.assertTrue(all(len(texto) <= 3900 for texto in textos))

        galerias = [
            item for item in container.children
            if isinstance(item, discord.ui.MediaGallery)
        ]
        self.assertEqual(len(galerias), 1)
        self.assertEqual(len(galerias[0].items), 2)

    def test_reconstrucao_de_preferencias_preserva_todos_os_blocos_e_botoes(self):
        original = discord.ui.LayoutView(timeout=None)
        botao_preferencias = AlternarAvisosButton()
        botao_preferencias.row = None
        atalho = discord.ui.Button(
            label="Ver sistemas",
            style=discord.ButtonStyle.link,
            url="https://discord.com/channels/1/2",
        )
        original.add_item(discord.ui.Container(
            discord.ui.TextDisplay("A" * 4000),
            discord.ui.TextDisplay("B" * 1200),
            discord.ui.ActionRow(atalho),
            discord.ui.ActionRow(botao_preferencias),
        ))
        mensagem = Mock()
        mensagem.components = original.children
        mensagem.embeds = []

        reconstruido = _reconstruir_cartao_preferencias(
            mensagem, botao_preferencias
        )

        self.assertIsInstance(reconstruido, discord.ui.LayoutView)
        container = reconstruido.children[0]
        self.assertIsInstance(container, discord.ui.Container)
        textos = _textos_do_container(container)
        self.assertEqual(
            "".join(textos[:-1]),
            ("A" * 4000) + "\n\n" + ("B" * 1200),
        )
        self.assertEqual(textos[-1], "-# Nêmesis Systeam")
        self.assertTrue(all(len(texto) <= 3900 for texto in textos))

        botoes = _botoes_do_container(container)
        self.assertEqual(
            [botao.url for botao in botoes if botao.url],
            ["https://discord.com/channels/1/2"],
        )
        alternar = next(
            botao for botao in botoes
            if botao.custom_id == botao_preferencias.custom_id
        )
        self.assertEqual(alternar.custom_id, "nemesis:alternar_notas_dm")
        self.assertIsNotNone(alternar.callback)

    def test_cartao_boas_vindas_preserva_texto_imagem_e_controles_aninhados(self):
        embed = discord.Embed(
            title="Boas-vindas",
            description="Etapa completa.\n" * 320,
        )
        embed.set_thumbnail(url="https://example.com/avatar.png")
        membro = Mock()

        with patch("cogs.boas_vindas_dm._embed_inicio", return_value=embed):
            view = BoasVindasLayoutView(membro, 987)

        container = view.children[0]
        self.assertIsInstance(container, discord.ui.Container)
        textos = _textos_do_container(container)
        self.assertEqual("".join(textos[:-1]), texto_embed_components_v2(embed))
        self.assertEqual(textos[-1], "-# NÊMESIS • INTEGRAÇÃO OFICIAL • NΞM")
        self.assertTrue(all(len(texto) <= 3900 for texto in textos))
        self.assertTrue(any(
            isinstance(item, discord.ui.MediaGallery)
            for item in container.children
        ))
        linhas = [
            item for item in container.children
            if isinstance(item, discord.ui.ActionRow)
        ]
        self.assertEqual(len(linhas), 3)
        self.assertTrue(any(
            isinstance(controle, discord.ui.Select)
            for linha in linhas for controle in linha.children
        ))
        self.assertTrue(any(
            isinstance(controle, discord.ui.Button)
            for linha in linhas for controle in linha.children
        ))

    def test_reconstrucao_de_embed_legada_preserva_imagem_e_conteudo_longo(self):
        original = discord.ui.View(timeout=None)
        botao = AlternarAvisosButton()
        original.add_item(botao)

        embed = discord.Embed(
            title="Notas antigas",
            description="Conteúdo preservado.\n" * 260,
        )
        embed.set_image(url="https://example.com/arquivo.png")
        embed.set_footer(text="Nêmesis Systeam")
        mensagem = Mock()
        mensagem.components = []
        mensagem.embeds = [embed]

        reconstruido = _reconstruir_cartao_preferencias(mensagem, botao)

        container = reconstruido.children[0]
        textos = _textos_do_container(container)
        self.assertEqual("".join(textos), texto_embed_components_v2(embed))
        self.assertTrue(all(len(texto) <= 3900 for texto in textos))
        galerias = [
            item for item in container.children
            if isinstance(item, discord.ui.MediaGallery)
        ]
        self.assertEqual(len(galerias), 1)
        self.assertEqual(len(galerias[0].items), 1)


if __name__ == "__main__":
    unittest.main()
