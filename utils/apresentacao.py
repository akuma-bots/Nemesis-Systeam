"""Sistema visual unificado da Chaos Org para embeds do Discord.

A camada aplica identidade visual visível a todas as embeds que usam criar_embed,
sem substituir a informação específica, os campos ou as ações de cada sistema.
"""
from __future__ import annotations

import discord

COR_PRIMARIA = 0x8B1E2D  # Carmesim escuro Chaos Org
COR_SUCESSO = 0x2D9D78
COR_AVISO = 0xD69E2E
COR_ERRO = 0x7F1D2D
COR_NEUTRA = 0x111014
MARCA = "Chaos Org"
AUTOR_PADRAO = "Chaos Org • CENTRAL DE SISTEMAS"
RODAPE_PADRAO = "Chaos Org • SISTEMAS INTEGRADOS"
ASSINATURA_SISTEMA = "Chaos Systeam"


def criar_embed(
    title: str | None = None,
    description: str | None = None,
    *,
    cor: int | None = None,
    rodape: str | None = RODAPE_PADRAO,
    **kwargs,
) -> discord.Embed:
    """Cria uma embed com cabeçalho, título e assinatura visual da Chaos Org."""
    if cor is not None:
        kwargs["color"] = cor
    elif "color" not in kwargs and "colour" not in kwargs:
        kwargs["color"] = COR_PRIMARIA

    if isinstance(kwargs.get("timestamp"), bool):
        kwargs["timestamp"] = discord.utils.utcnow() if kwargs["timestamp"] else None

    # Todos os sistemas recebem timestamp por padrão; chamadas explícitas
    # ainda podem desligá-lo com timestamp=None.
    if "timestamp" not in kwargs:
        kwargs["timestamp"] = discord.utils.utcnow()

    # Títulos objetivos e legíveis: a identidade fica no autor, no rodapé
    # e nas cores, sem fontes artificiais ou molduras repetitivas.
    if title:
        title = " ".join(title.strip().split())[:256]

    embed = discord.Embed(title=title, description=description, **kwargs)

    # Autor e rodapé criam uma assinatura visual consistente mesmo quando o
    # sistema define um rodapé próprio.
    if not embed.author.name:
        embed.set_author(name=AUTOR_PADRAO)

    # Assinatura discreta e consistente em todos os painéis e respostas
    # que utilizam esta camada compartilhada de apresentação.
    if rodape:
        texto_rodape = str(rodape).strip()
        if ASSINATURA_SISTEMA.casefold() not in texto_rodape.casefold():
            texto_rodape = f"{texto_rodape} • {ASSINATURA_SISTEMA}"
        embed.set_footer(text=texto_rodape[:2048])

    return embed



def dividir_texto_components_v2(texto: str, limite: int = 3900) -> list[str]:
    """Divide texto em blocos seguros para TextDisplay sem descartar caracteres."""
    texto = str(texto or "")
    limite = int(limite)
    if limite < 1 or limite > 4000:
        raise ValueError("O limite de TextDisplay deve ficar entre 1 e 4000 caracteres.")
    if not texto:
        return [""]

    partes = []
    inicio = 0
    while inicio < len(texto):
        fim = min(inicio + limite, len(texto))
        if fim < len(texto):
            quebra = texto.rfind("\n", inicio, fim)
            if quebra > inicio:
                fim = quebra + 1
        partes.append(texto[inicio:fim])
        inicio = fim
    return partes


def texto_embed_components_v2(embed: discord.Embed) -> str:
    """Converte os elementos textuais de uma embed em texto integral para Components V2."""
    partes = []
    autor = embed.author
    if autor and autor.name:
        nome_autor = f"[{autor.name}]({autor.url})" if autor.url else autor.name
        partes.append(f"**{nome_autor}**")

    if embed.title:
        titulo = f"[{embed.title}]({embed.url})" if embed.url else embed.title
        partes.append(f"## {titulo}")
    if embed.description:
        partes.append(embed.description)

    for campo in embed.fields:
        partes.append(f"**{campo.name}**\n{campo.value}")

    if embed.footer and embed.footer.text:
        partes.append(f"-# {embed.footer.text}")
    if embed.timestamp:
        partes.append(f"-# {discord.utils.format_dt(embed.timestamp, style='F')}")

    return "\n\n".join(partes)


def imagens_embed_components_v2(embed: discord.Embed) -> list[tuple[str, str]]:
    """Retorna miniatura e imagem da embed, sem duplicar a mesma URL."""
    imagens = []
    vistas = set()
    for atributo, descricao in (
        ("thumbnail", "Miniatura do comunicado"),
        ("image", "Imagem do comunicado"),
    ):
        url = getattr(getattr(embed, atributo, None), "url", None)
        if url and url not in vistas:
            vistas.add(url)
            imagens.append((str(url), descricao))
    return imagens


def cor_por_estado(sucesso: bool, *, aviso: bool = False) -> int:
    if sucesso:
        return COR_SUCESSO
    return COR_AVISO if aviso else COR_ERRO


def embed_sucesso(titulo: str, descricao: str, **kwargs) -> discord.Embed:
    return criar_embed(titulo, descricao, cor=COR_SUCESSO, **kwargs)


def embed_erro(titulo: str, descricao: str, **kwargs) -> discord.Embed:
    return criar_embed(titulo, descricao, cor=COR_ERRO, **kwargs)


def embed_aviso(titulo: str, descricao: str, **kwargs) -> discord.Embed:
    return criar_embed(titulo, descricao, cor=COR_AVISO, **kwargs)


def embed_info(titulo: str, descricao: str, **kwargs) -> discord.Embed:
    return criar_embed(titulo, descricao, cor=COR_PRIMARIA, **kwargs)



def aplicar_identidade_servidor(
    embed: discord.Embed,
    guild: discord.Guild | None,
    bot: discord.Client | None = None,
    *,
    banner: bool = True,
) -> discord.Embed:
    """Aplica banner, ícone do servidor e avatar do bot sem exigir assets configurados."""
    if guild is None:
        return embed

    icone = getattr(guild, "icon", None)
    icone_servidor = icone.url if icone else None
    avatar_bot = None
    usuario_bot = getattr(bot, "user", None) if bot else None
    if usuario_bot:
        avatar = getattr(usuario_bot, "display_avatar", None)
        avatar_bot = avatar.url if avatar else None

    # O ícone do servidor identifica a organização; o avatar do bot assina o painel.
    if icone_servidor:
        embed.set_thumbnail(url=icone_servidor)
    elif avatar_bot:
        embed.set_thumbnail(url=avatar_bot)

    if avatar_bot:
        autor = embed.author
        # discord.py atual não expõe discord.Embed.Empty. O argumento url é
        # opcional; omiti-lo quando não existe evita falha em runtime.
        autor_kwargs = {
            "name": autor.name or "N̷ÊMESIS  •  CENTRAL DE SISTEMAS",
            "icon_url": avatar_bot,
        }
        if autor.url:
            autor_kwargs["url"] = autor.url
        embed.set_author(**autor_kwargs)

    banner_servidor = getattr(guild, "banner", None)
    if banner and banner_servidor:
        embed.set_image(url=banner_servidor.url)

    return embed
