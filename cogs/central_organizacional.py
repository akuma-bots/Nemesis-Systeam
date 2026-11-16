import logging
import os

import discord
from discord.ext import commands

from utils.storage import carregar, salvar

_LOG = logging.getLogger(__name__)
GUILD_ID = int(os.getenv("NEMESIS_GUILD_ID", "1563995879981981817"))
CANAL_HIERARQUIA_ID = 1563995880833421511
ARQUIVO_ESTADO = "central_hierarquia_nemesis.json"
MARCADOR = "NÊMESIS • CENTRAL ORGANIZACIONAL • V1"

CARGO_OCTOGONO_ID = 1563995880007139425
CARGO_SUPERVISOR_STAFF_ID = 1563995880007139422
CARGOS_DIRECAO_STAFF_IDS = {
    1563995880007139424,
    1563995880007139423,
}
CARGOS_ACIMA_ELITE_IDS = {
    1563995879998754938,
    1563995879998754939,
    1563995879998754940,
    1563995879998754941,
    1563995879998754942,
    1563995879998754943,
}


def _limitar(texto: str, limite: int = 3900) -> str:
    texto = str(texto or "")
    if len(texto) <= limite:
        return texto
    return texto[:limite - 24].rsplit("\n", 1)[0] + "\n… conteúdo resumido."


def _cargo(guild: discord.Guild, cargo_id: int, nome: str) -> str:
    cargo = guild.get_role(cargo_id)
    return cargo.mention if cargo else f"**{nome}**"

def _pagina_hierarquia(guild: discord.Guild) -> str:
    progressao = (
        (1563995879998754943, "Capitão Geral", 1),
        (1563995879998754942, "Capitão", 2),
        (1563995879998754941, "Vice Capitão", 3),
        (1563995879998754940, "Comandante", 4),
        (1563995879998754939, "Treinador", 5),
        (1563995879998754938, "Veterano", 6),
        (1563995879995874937, "Elite", 7),
        (1563995879990624377, "Especialista", 8),
        (1563995879990624376, "Executor", 9),
        (1563995879990624375, "Tenente", 10),
        (1563995879990624374, "Subtenente", 11),
        (1563995879990624373, "Lutador", 12),
    )
    linhas = ["## 𓂀 HIERARQUIA NÊMESIS", "Estrutura oficial de cargos e progressão, da maior patente à inicial.", "", "**IDENTIDADE ORGANIZACIONAL**", _cargo(guild, 1563995879990624372, "NÊMESIS"), "", "**PROGRESSÃO DE PATENTES**"]
    linhas.extend(f"**{numero:02d}.** {_cargo(guild, cargo_id, nome)}" for cargo_id, nome, numero in progressao)
    linhas.extend(["", "**CRITÉRIOS DE AUTORIDADE**", "• Veterano ou patente superior pode promover, rebaixar e banir, respeitando a hierarquia do alvo.", "• Ações hierárquicas exigem justificativa e registro.", "• Cargos administrativos são apresentados em suas próprias áreas e não se confundem com a progressão.", "", "-# A progressão é vinculada ao XP organizacional; o sistema competitivo permanece independente."])
    return _limitar("\\n".join(linhas))

def _pagina_divisoes(guild: discord.Guild) -> str:
    divisoes = ("N1 Alpha", "N2 Vanguard", "N3 Elite", "N4 Recon", "N5 Assault", "N6 Guard")
    linhas = ["## ⚔️ DIVISÕES", "Núcleos próprios dentro da NÊMESIS. A hierarquia interna das divisões permanece nesta área.", "", "**ESTRUTURA DAS DIVISÕES**"]
    for nome in divisoes:
        cargo = discord.utils.find(lambda item: item.name.casefold() == nome.casefold(), guild.roles)
        linhas.append(f"• {cargo.mention if cargo else f\"**{nome}**\"}")
    linhas.extend(["", "**LIDERANÇA E ORGANIZAÇÃO**", "A liderança de cada divisão será exibida quando os respectivos responsáveis e cargos oficiais estiverem definidos.", "• Cargos gerais da NÊMESIS, Staffs e OCTÓGONO não são repetidos nesta lista.", "", "-# Nenhuma chefia ou permissão é atribuída automaticamente por esta central."])
    return _limitar("\\n".join(linhas))

def _pagina_staffs(guild: discord.Guild) -> str:
    cargos = ((1563995880007139424, "Diretor Staff"), (1563995880007139423, "Vice-Diretor Staff"), (1563995880007139422, "Supervisor Staff"))
    linhas = ["## ♟️ STAFFS", "Núcleo administrativo responsável pela organização, acompanhamento e suporte institucional.", "", "**ESTRUTURA ADMINISTRATIVA**"]
    linhas.extend(f"• {_cargo(guild, cargo_id, nome)}" for cargo_id, nome in cargos)
    linhas.extend(["", "**RESPONSABILIDADES**", "• Diretor e Vice-Diretor Staff: apoio à condução administrativa.", "• Supervisor Staff: possui permissões administrativas gerais.", "• A equipe acompanha demandas, orienta membros e encaminha decisões aos responsáveis.", "", "-# Permissões administrativas não concedem automaticamente gestão de missões ou ações de progressão."])
    return _limitar("\\n".join(linhas))

def _pagina_octogono(guild: discord.Guild) -> str:
    linhas = ["## 🔰 OCTÓGONO", "Núcleo responsável pela gestão exclusiva das missões da NÊMESIS.", "", "**CARGO RESPONSÁVEL**", _cargo(guild, 1563995880007139425, "OCTÓGONO"), "", "**ATRIBUIÇÕES**", "• Gerenciar missões, contribuições e operações especiais.", "• Analisar provas e validar resultados das atividades sob sua responsabilidade.", "• Acompanhar a execução das operações e a aplicação das recompensas.", "• Manter registros e decisões fundamentadas.", "", "**LIMITE DE AUTORIDADE**", "A gestão de missões é exclusiva do OCTÓGONO. As permissões administrativas gerais e as ações de progressão seguem suas próprias regras.", "", "-# Esta página informa atribuições; não concede permissões por si só."]
    return _limitar("\\n".join(linhas))

PAGINAS = {
    "hierarquia": ("𓂀 Hierarquia Nêmesis", "🏛️", _pagina_hierarquia),
    "divisoes": ("Divisões", "⚔️", _pagina_divisoes),
    "staffs": ("Staffs", "♟️", _pagina_staffs),
    "octogono": ("OCTÓGONO", "🔰", _pagina_octogono),
}


class SeletorHierarquia(discord.ui.Select):
    def __init__(self, selecionado: str = "hierarquia"):
        super().__init__(
            placeholder="Selecione uma área da organização",
            min_values=1,
            max_values=1,
            custom_id="nemesis:central_organizacional:seletor:v1",
            options=[
                discord.SelectOption(label=nome, value=chave, emoji=emoji, default=(chave == selecionado))
                for chave, (nome, emoji, _) in PAGINAS.items()
            ],
        )

    async def callback(self, interaction: discord.Interaction):
        if interaction.guild_id != GUILD_ID or interaction.guild is None:
            await interaction.response.send_message("Esta central pertence à NÊMESIS.", ephemeral=True)
            return
        chave = self.values[0]
        nome, emoji, renderizar = PAGINAS[chave]
        texto = renderizar(interaction.guild)
        view = CentralOrganizacionalView(chave=chave, texto=texto)
        await interaction.response.edit_message(view=view)


class CentralOrganizacionalView(discord.ui.LayoutView):
    def __init__(self, chave: str = "hierarquia", texto: str | None = None):
        super().__init__(timeout=None)
        nome, emoji, renderizar = PAGINAS[chave]
        seletor = SeletorHierarquia(chave)
        if texto is None:
            texto = (
                "## 𓂀 NÊMESIS • CENTRAL ORGANIZACIONAL\n"
                "Consulte a estrutura da organização, suas equipes e seus núcleos de responsabilidade. "
                "Selecione uma categoria abaixo para alternar o conteúdo."
            )
        self.add_item(discord.ui.Container(
            discord.ui.TextDisplay(texto),
            discord.ui.Separator(visible=True, spacing=discord.SeparatorSpacing.small),
            discord.ui.TextDisplay("**CONSULTAR OUTRA ÁREA**"),
            discord.ui.ActionRow(seletor),
            discord.ui.Separator(visible=True, spacing=discord.SeparatorSpacing.small),
            discord.ui.TextDisplay(f"-# {MARCADOR}"),
            accent_colour=0x991B33,
        ))


class CentralOrganizacional(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self._sincronizada = False
        self._lock = __import__("asyncio").Lock()
        self.bot.add_view(CentralOrganizacionalView())

    @commands.Cog.listener()
    async def on_ready(self):
        if self._sincronizada:
            return
        async with self._lock:
            if self._sincronizada:
                return
            guild = self.bot.get_guild(GUILD_ID)
            if guild is None:
                _LOG.warning("Servidor NÊMESIS indisponível; central organizacional aguardará reconexão.")
                return
            canal = guild.get_channel(CANAL_HIERARQUIA_ID)
            if canal is None:
                try:
                    canal = await self.bot.fetch_channel(CANAL_HIERARQUIA_ID)
                except discord.HTTPException:
                    _LOG.exception("Não foi possível localizar o canal da central organizacional.")
                    return
            if not isinstance(canal, discord.TextChannel) or canal.guild.id != GUILD_ID:
                _LOG.error("Canal %s não é um canal de texto válido da NÊMESIS.", CANAL_HIERARQUIA_ID)
                return
            permissoes = canal.permissions_for(guild.me)
            if not (permissoes.view_channel and permissoes.send_messages and permissoes.read_message_history):
                _LOG.error("Permissões insuficientes para manter a central organizacional.")
                return
            estado = await carregar(ARQUIVO_ESTADO, {"message_id": None})
            mensagem = None
            message_id = estado.get("message_id") if isinstance(estado, dict) else None
            if message_id:
                try:
                    mensagem = await canal.fetch_message(int(message_id))
                except discord.NotFound:
                    mensagem = None
                except discord.HTTPException:
                    _LOG.exception("Falha ao recuperar a mensagem da central organizacional.")
                    return
            if mensagem is None:
                async for antiga in canal.history(limit=100):
                    if antiga.author.id != self.bot.user.id:
                        continue
                    if any(MARCADOR in str(getattr(c, "content", "")) for c in antiga.components):
                        mensagem = antiga
                        break
            view = CentralOrganizacionalView(texto=_pagina_hierarquia(guild))
            if mensagem is None:
                mensagem = await canal.send(view=view, allowed_mentions=discord.AllowedMentions.none())
            else:
                await mensagem.edit(content=None, embeds=[], attachments=[], view=view,
                                    allowed_mentions=discord.AllowedMentions.none())
            await salvar(ARQUIVO_ESTADO, {"guild_id": GUILD_ID, "message_id": mensagem.id})
            self._sincronizada = True
            _LOG.info("Central Organizacional sincronizada (canal=%s, mensagem=%s).", canal.id, mensagem.id)


async def setup(bot: commands.Bot):
    await bot.add_cog(CentralOrganizacional(bot))
