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
        (1563995879998754943, "Capitão Geral", 1,
         "Direção estratégica da NÊMESIS. Define prioridades, estabelece diretrizes e responde pela condução geral da organização."),
        (1563995879998754942, "Capitão", 2,
         "Compartilha a condução estratégica, acompanha as lideranças e assegura a execução das decisões superiores."),
        (1563995879998754941, "Vice Capitão", 3,
         "Presta apoio direto ao comando, acompanha demandas internas e assume atribuições de liderança quando necessário."),
        (1563995879998754940, "Comandante", 4,
         "Coordena a execução das atividades, orienta integrantes e mantém a organização das operações sob sua responsabilidade."),
        (1563995879998754939, "Treinador", 5,
         "Conduz a preparação dos integrantes, transmite conhecimentos e acompanha o desenvolvimento técnico e operacional."),
        (1563995879998754938, "Veterano", 6,
         "Oferece orientação com base na experiência, auxilia os demais integrantes e contribui para preservar os padrões da organização."),
        (1563995879995874937, "Elite", 7,
         "Representa um nível elevado de desempenho e consistência, servindo como referência de comprometimento e qualidade."),
        (1563995879990624377, "Especialista", 8,
         "Aplica conhecimentos específicos, apoia atividades que exigem domínio técnico e contribui para o aperfeiçoamento coletivo."),
        (1563995879990624376, "Executor", 9,
         "Transforma orientações em ações, cumpre tarefas designadas e mantém a qualidade das entregas operacionais."),
        (1563995879990624375, "Tenente", 10,
         "Apoia a coordenação cotidiana, acompanha a execução das orientações e auxilia na organização dos integrantes."),
        (1563995879990624374, "Subtenente", 11,
         "Presta suporte às atividades internas, auxilia na comunicação e demonstra preparo para assumir novas responsabilidades."),
        (1563995879990624373, "Lutador", 12,
         "Integra a base ativa da organização. Participa das atividades, desenvolve suas habilidades e consolida sua trajetória na NÊMESIS."),
    )
    linhas = [
        "## 𓂀 NÊMESIS • HIERARQUIA INSTITUCIONAL",
        "Uma estrutura de progressão que reconhece experiência, desempenho e responsabilidade. Cada patente possui atribuições próprias e contribui para a continuidade da organização.",
        "",
        "**IDENTIDADE ORGANIZACIONAL**",
        _cargo(guild, 1563995879990624372, "NÊMESIS"),
        "",
        "━━━━━━━━━━━━━━━━━━━━",
        "**PATENTES • FUNÇÕES E RESPONSABILIDADES**",
        "",
    ]
    for cargo_id, nome, numero, descricao in progressao:
        linhas.extend([
            f"**{numero:02d} • {nome.upper()}**",
            f"**Função:** {descricao.split('.')[0]}.",
            f"**Descrição:** {descricao}",
            "",
            "━━━━━━━━━━━━━━━━━━━━",
            "",
        ])
    linhas.extend([
        "**AUTORIDADE E CONDUTA**",
        "• Veterano e patentes superiores estão autorizados a promover, rebaixar e banir, sempre respeitando a posição hierárquica do alvo.",
        "• Ações hierárquicas exigem justificativa e registro.",
        "• Diretorias Staff e OCTÓGONO possuem áreas próprias e não são níveis desta progressão.",
        "",
        "-# A progressão é vinculada ao XP organizacional. O sistema competitivo permanece independente.",
        "-# NÊMESIS — Authority Beyond Rank.",
    ])
    return _limitar("\\n".join(linhas), limite=3900)

def _pagina_divisoes(guild: discord.Guild) -> str:
    divisoes = ("N1 Alpha", "N2 Vanguard", "N3 Elite", "N4 Recon", "N5 Assault", "N6 Guard")
    linhas = ["## ⚔️ DIVISÕES", "Núcleos próprios dentro da NÊMESIS. A hierarquia interna das divisões permanece nesta área.", "", "**ESTRUTURA DAS DIVISÕES**"]
    for nome in divisoes:
        cargo = discord.utils.find(lambda item: item.name.casefold() == nome.casefold(), guild.roles)
        identificacao = cargo.mention if cargo else f"**{nome}**"
        linhas.append(f"• {identificacao}")
    linhas.extend(["", "**LIDERANÇA E ORGANIZAÇÃO**", "A liderança de cada divisão será exibida quando os respectivos responsáveis e cargos oficiais estiverem definidos.", "• Cargos gerais da NÊMESIS, Staffs e OCTÓGONO não são repetidos nesta lista.", "", "-# Nenhuma chefia ou permissão é atribuída automaticamente por esta central."])
    return _limitar("\n".join(linhas))

def _pagina_staffs(guild: discord.Guild) -> str:
    cargos = ((1563995880007139424, "Diretor Staff"), (1563995880007139423, "Vice-Diretor Staff"), (1563995880007139422, "Supervisor Staff"))
    linhas = ["## ♟️ STAFFS", "Núcleo administrativo responsável pela organização, acompanhamento e suporte institucional.", "", "**ESTRUTURA ADMINISTRATIVA**"]
    linhas.extend(f"• {_cargo(guild, cargo_id, nome)}" for cargo_id, nome in cargos)
    linhas.extend(["", "**RESPONSABILIDADES**", "• Diretor e Vice-Diretor Staff: apoio à condução administrativa.", "• Supervisor Staff: possui permissões administrativas gerais.", "• A equipe acompanha demandas, orienta membros e encaminha decisões aos responsáveis.", "", "-# Permissões administrativas não concedem automaticamente gestão de missões ou ações de progressão."])
    return _limitar("\n".join(linhas))

def _pagina_octogono(guild: discord.Guild) -> str:
    linhas = ["## 🔰 OCTÓGONO", "Núcleo responsável pela gestão exclusiva das missões da NÊMESIS.", "", "**CARGO RESPONSÁVEL**", _cargo(guild, 1563995880007139425, "OCTÓGONO"), "", "**ATRIBUIÇÕES**", "• Gerenciar missões, contribuições e operações especiais.", "• Analisar provas e validar resultados das atividades sob sua responsabilidade.", "• Acompanhar a execução das operações e a aplicação das recompensas.", "• Manter registros e decisões fundamentadas.", "", "**LIMITE DE AUTORIDADE**", "A gestão de missões é exclusiva do OCTÓGONO. As permissões administrativas gerais e as ações de progressão seguem suas próprias regras.", "", "-# Esta página informa atribuições; não concede permissões por si só."]
    return _limitar("\n".join(linhas))

PAGINAS = {
    "hierarquia": ("Hierarquia Nêmesis", None, _pagina_hierarquia),
    "divisoes": ("Divisões", None, _pagina_divisoes),
    "staffs": ("Hierarquia Staff", None, _pagina_staffs),
    "octogono": ("Hierarquia Octógono", None, _pagina_octogono),
}


class SeletorHierarquia(discord.ui.Select):
    def __init__(self, selecionado: str = "hierarquia"):
        super().__init__(
            placeholder="Selecione uma área da organização",
            min_values=1,
            max_values=1,
            custom_id="nemesis:central_organizacional:seletor:v1",
            options=[
                discord.SelectOption(label=nome, value=chave, default=(chave == selecionado))
                for chave, (nome, _emoji, _) in PAGINAS.items()
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
