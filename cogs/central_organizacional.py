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


def _cargos_hierarquia(guild: discord.Guild) -> list[discord.Role]:
    ignorar = {guild.default_role.id}
    return sorted(
        (cargo for cargo in guild.roles if cargo.id not in ignorar and not cargo.managed),
        key=lambda cargo: cargo.position,
        reverse=True,
    )


def _pagina_hierarquia(guild: discord.Guild) -> str:
    cargos = _cargos_hierarquia(guild)
    linhas = [
        "## 𓂀 HIERARQUIA NÊMESIS",
        "A estrutura oficial organiza autoridade, responsabilidade e progressão. A posição dos cargos no Discord determina a precedência hierárquica.",
        "",
        "**CARGOS E POSIÇÕES**",
    ]
    linhas.extend(f"• {cargo.mention}" for cargo in cargos[:45])
    if len(cargos) > 45:
        linhas.append(f"• + {len(cargos) - 45} cargos adicionais no servidor.")
    linhas.extend([
        "",
        "**DIRETRIZES DE AUTORIDADE**",
        "• Cargos acima de Elite podem promover, rebaixar e banir, respeitando a posição do alvo.",
        "• Supervisor Staff integra a administração, mas não recebe automaticamente poderes de promoção, rebaixamento ou banimento.",
        "• O OCTÓGONO possui atribuição exclusiva sobre a gestão de missões.",
        "",
        "-# Relação de cargos carregada diretamente da estrutura atual do servidor.",
    ])
    return _limitar("\n".join(linhas))


def _pagina_divisoes(guild: discord.Guild) -> str:
    termos = ("divisão", "divisao", "division", "esquadrão", "esquadrao")
    cargos = [
        cargo for cargo in _cargos_hierarquia(guild)
        if any(termo in cargo.name.casefold() for termo in termos)
    ]
    linhas = [
        "## ⚔️ DIVISÕES",
        "As divisões representam frentes de atuação da NÊMESIS. Cada uma deve seguir suas atribuições oficiais e a orientação de sua liderança.",
        "",
        "**DIVISÕES IDENTIFICADAS NO SERVIDOR**",
    ]
    if cargos:
        linhas.extend(f"• {cargo.mention}" for cargo in cargos)
    else:
        linhas.append("Ainda não há cargos com identificação explícita de divisão na lista de cargos do Discord.")
    linhas.extend([
        "",
        "**ORGANIZAÇÃO**",
        "• A liderança da divisão coordena sua equipe e acompanha a participação.",
        "• Os integrantes executam as atividades e objetivos definidos para sua divisão.",
        "• Atribuições específicas devem seguir as diretrizes oficiais publicadas pela organização.",
        "",
        "-# Esta página não cria divisões nem atribui chefias automaticamente.",
    ])
    return _limitar("\n".join(linhas))


def _pagina_staffs(guild: discord.Guild) -> str:
    ids = CARGOS_DIRECAO_STAFF_IDS | {CARGO_SUPERVISOR_STAFF_ID}
    cargos = [
        cargo for cargo in _cargos_hierarquia(guild)
        if cargo.id in ids or "staff" in cargo.name.casefold()
    ]
    linhas = [
        "## ♟️ STAFFS",
        "A equipe Staff apoia a administração, a organização interna e o funcionamento dos serviços da NÊMESIS.",
        "",
        "**ESTRUTURA STAFF**",
    ]
    linhas.extend(f"• {cargo.mention}" for cargo in cargos)
    if not cargos:
        linhas.append("Os cargos Staff não foram localizados no cache do servidor.")
    linhas.extend([
        "",
        "**RESPONSABILIDADES**",
        "• Direção e Vice-Direção Staff auxiliam na condução administrativa.",
        "• Supervisores Staff possuem permissões administrativas.",
        "• A equipe deve orientar membros, acompanhar demandas e encaminhar decisões aos responsáveis.",
        "• Acesso administrativo não altera as regras específicas de progressão ou gestão de missões.",
        "",
        "-# As permissões efetivas continuam definidas pelos sistemas e cargos oficiais.",
    ])
    return _limitar("\n".join(linhas))


def _pagina_octogono(guild: discord.Guild) -> str:
    cargo = guild.get_role(CARGO_OCTOGONO_ID)
    linhas = [
        "## ⬡ OCTÓGONO",
        "Núcleo responsável pela condução e gestão das operações de missões da NÊMESIS.",
        "",
        "**CARGO RESPONSÁVEL**",
        cargo.mention if cargo else "Cargo OCTÓGONO não localizado no cache do servidor.",
        "",
        "**ATRIBUIÇÕES**",
        "• Gerenciar missões, contribuições e operações especiais.",
        "• Analisar provas e validar resultados das atividades sob sua responsabilidade.",
        "• Acompanhar a execução das operações e a aplicação correta das recompensas.",
        "• Manter registros e decisões fundamentadas.",
        "",
        "**LIMITE DE AUTORIDADE**",
        "A gestão de missões é exclusiva do OCTÓGONO. A administração geral e as ações hierárquicas seguem suas próprias permissões.",
        "",
        "-# A página informa atribuições; não concede permissões por si só.",
    ]
    return _limitar("\n".join(linhas))


PAGINAS = {
    "hierarquia": ("𓂀 Hierarquia Nêmesis", "🏛️", _pagina_hierarquia),
    "divisoes": ("Divisões", "⚔️", _pagina_divisoes),
    "staffs": ("Staffs", "♟️", _pagina_staffs),
    "octogono": ("OCTÓGONO", "⬡", _pagina_octogono),
}


class SeletorHierarquia(discord.ui.Select):
    def __init__(self):
        super().__init__(
            placeholder="Selecione uma área da organização",
            min_values=1,
            max_values=1,
            custom_id="nemesis:central_organizacional:seletor:v1",
            options=[
                discord.SelectOption(label=nome, value=chave, emoji=emoji, default=(chave == "hierarquia"))
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
        seletor = SeletorHierarquia()
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
            view = CentralOrganizacionalView()
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
