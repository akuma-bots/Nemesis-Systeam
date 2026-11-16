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
        (1563995879998754943, "Capitão Geral", 1, "Direção estratégica", "Define diretrizes, estabelece prioridades e responde pela condução geral da NÊMESIS."),
        (1563995879998754942, "Capitão", 2, "Comando superior", "Acompanha as lideranças e assegura que as decisões estratégicas sejam executadas."),
        (1563995879998754941, "Vice Capitão", 3, "Apoio ao comando", "Auxilia diretamente a liderança e assume atribuições de comando quando necessário."),
        (1563995879998754940, "Comandante", 4, "Coordenação operacional", "Organiza atividades, orienta integrantes e acompanha a execução das operações."),
        (1563995879998754939, "Treinador", 5, "Formação de integrantes", "Prepara membros, transmite conhecimentos e acompanha o desenvolvimento técnico."),
        (1563995879998754938, "Veterano", 6, "Orientação e experiência", "Compartilha experiência, orienta integrantes e contribui para manter os padrões da organização."),
        (1563995879998754937, "Elite", 7, "Excelência e referência", "Representa alto desempenho, consistência e comprometimento com a NÊMESIS."),
        (1563995879990624377, "Especialista", 8, "Domínio técnico", "Aplica conhecimentos específicos e auxilia no aperfeiçoamento das atividades."),
        (1563995879990624376, "Executor", 9, "Execução de diretrizes", "Transforma orientações em ações e cumpre as tarefas sob sua responsabilidade."),
        (1563995879990624375, "Tenente", 10, "Apoio à coordenação", "Acompanha atividades, auxilia na organização dos integrantes e reforça as orientações superiores."),
        (1563995879990624374, "Subtenente", 11, "Suporte interno", "Apoia a rotina da organização, facilita a comunicação e desenvolve capacidade de liderança."),
        (1563995879990624373, "Lutador", 12, "Participação e evolução", "Integra a base ativa, participa das atividades e desenvolve sua trajetória na NÊMESIS."),
    )
    linhas = [
        "## 𓂀 NÊMESIS • HIERARQUIA INSTITUCIONAL",
        "Conheça as patentes, suas funções e responsabilidades. Cada posição representa uma etapa de experiência, desempenho e compromisso com a organização.",
        "",
        "**IDENTIDADE ORGANIZACIONAL**",
        _cargo(guild, 1563995879990624372, "NÊMESIS"),
        "",
        "━━━━━━━━━━━━━━━━━━━━",
        "**PATENTES • FUNÇÕES E RESPONSABILIDADES**",
        "",
    ]
    for cargo_id, nome, numero, funcao, descricao in progressao:
        linhas.extend([
            f"**{numero:02d} • {_cargo(guild, cargo_id, nome)}**",
            f"**Função:** {funcao}.",
            f"**Descrição:** {descricao}",
            "",
            "━━━━━━━━━━━━━━━━━━━━",
            "",
        ])
    linhas.extend([
        "**AUTORIDADE E CONDUTA**",
        "• Veterano e patentes superiores estão autorizados a promover, rebaixar e banir, respeitando a hierarquia do alvo.",
        "• Ações hierárquicas exigem justificativa e registro.",
        "• Staff e OCTÓGONO possuem hierarquias próprias e não integram esta progressão.",
        "",
        "-# A progressão é vinculada ao XP organizacional. O sistema competitivo permanece independente.",
        "-# NÊMESIS — Authority Beyond Rank.",
    ])
    return _limitar("\n".join(linhas), limite=3900)

def _pagina_divisoes(guild: discord.Guild) -> str:
    divisoes = (
        (1563995879981981824, "N̷1 - Alpha"),
        (1563995879981981823, "N̷2 - Vanguard"),
        (1563995879981981822, "N̷3 - Elite"),
        (1563995879981981821, "N̷4 - Recon"),
        (1563995879981981820, "N̷5 - Assault"),
        (1563995879981981819, "N̷6 - Guard"),
    )
    linhas = ["## ⚔️ DIVISÕES", "Núcleos próprios dentro da NÊMESIS. A hierarquia interna das divisões permanece nesta área.", "", "**ESTRUTURA DAS DIVISÕES**"]
    for cargo_id, nome in divisoes:
        cargo = guild.get_role(cargo_id)
        identificacao = cargo.mention if cargo else f"⚠️ **{nome}** — cargo não localizado"
        linhas.append(f"• {identificacao}")
    linhas.extend(["", "**LIDERANÇA E ORGANIZAÇÃO**", "A liderança de cada divisão será exibida quando os respectivos responsáveis e cargos oficiais estiverem definidos.", "• Cargos gerais da NÊMESIS, Staffs e OCTÓGONO não são repetidos nesta lista.", "", "-# Nenhuma chefia ou permissão é atribuída automaticamente por esta central."])
    return _limitar("\n".join(linhas))

def _cargo_por_nome(guild: discord.Guild, nome: str, cargo_id: int | None = None) -> str:
    cargo = guild.get_role(cargo_id) if cargo_id else None
    if cargo is None:
        cargo = discord.utils.find(lambda item: item.name.casefold() == nome.casefold(), guild.roles)
    return cargo.mention if cargo else f"⚠️ **{nome}** — cargo ainda não localizado no servidor"


def _pagina_staffs(guild: discord.Guild) -> str:
    cargos = (
        (1563995880007139424, "Diretor Staff", "Direção administrativa",
         "Define prioridades da equipe, supervisiona a estrutura Staff e responde pela condução administrativa."),
        (1563995880007139423, "Vice-Diretor Staff", "Apoio à direção",
         "Auxilia o Diretor Staff, acompanha as demandas da equipe e mantém a continuidade da gestão."),
        (1563995880007139422, "Supervisor Staff", "Supervisão administrativa",
         "Supervisiona a atuação da equipe, acompanha procedimentos e possui permissões administrativas gerais."),
        (1563995880007139421, "Moderador Senior", "Coordenação da moderação",
         "Orienta os moderadores, acompanha ocorrências complexas e assegura a aplicação consistente das regras."),
        (1563995880007139420, "Moderador", "Moderação e ordem",
         "Atua na prevenção e resolução de conflitos, orienta membros e aplica as medidas previstas nas regras."),
        (1563995880007139419, "Assistente de Moderação", "Suporte à moderação",
         "Auxilia a equipe em atendimentos e ocorrências, reúne informações e encaminha situações aos responsáveis."),
        (1563995879998754946, "Agente de Atendimento", "Atendimento aos membros",
         "Recebe solicitações, esclarece dúvidas e direciona cada demanda ao setor responsável."),
        (1563995879998754945, "Estagiário Staff", "Aprendizado e apoio",
         "Conhece os procedimentos internos, acompanha a equipe e realiza tarefas de apoio sob orientação."),
    )
    linhas = [
        "## ♟️ NÊMESIS • HIERARQUIA STAFF",
        "Estrutura administrativa responsável pela organização, moderação, atendimento e suporte aos membros.",
        "",
        "**CARGOS • FUNÇÕES E RESPONSABILIDADES**",
        "",
    ]
    for numero, (cargo_id, nome, funcao, descricao) in enumerate(cargos, 1):
        linhas.extend([
            f"**{numero:02d} • {_cargo_por_nome(guild, nome, cargo_id)}**",
            f"**Função:** {funcao}.",
            f"**Descrição:** {descricao}",
            "",
            "━━━━━━━━━━━━━━━━━━━━",
            "",
        ])
    linhas.extend([
        "**DIRETRIZES ADMINISTRATIVAS**",
        "• Diretor Staff, Vice-Diretor Staff e Supervisor Staff integram a liderança administrativa.",
        "• O Supervisor Staff também possui permissões administrativas gerais.",
        "• A atuação da equipe deve respeitar os limites de cada função e os procedimentos da organização.",
        "• A hierarquia Staff não substitui a autoridade exclusiva do OCTÓGONO sobre a gestão de missões.",
        "",
        "-# Esta apresentação descreve atribuições; permissões são definidas separadamente pela configuração do servidor.",
        "-# NÊMESIS — Authority Beyond Rank.",
    ])
    return _limitar("\n".join(linhas), limite=3900)


def _pagina_octogono(guild: discord.Guild) -> str:
    cargos = (
        (1563995880015536193, "Æternum", "Direção e deliberação", "Representa a posição de referência do OCTÓGONO, zelando pela orientação estratégica e pela continuidade das decisões do núcleo."),
        (1563995880015536192, "Armageddon", "Condução de operações", "Atua na organização das operações e no acompanhamento das missões atribuídas ao OCTÓGONO."),
        (1563995880015536191, "Cataclysm", "Planejamento de missões", "Contribui para estruturar objetivos, etapas e critérios de execução das missões."),
        (1563995880015536190, "Pandæmonium", "Coordenação de atividades", "Auxilia na organização das atividades e na articulação dos integrantes envolvidos nas operações."),
        (1563995880015536189, "Oblivion", "Análise e validação", "Examina provas, registros e resultados, observando os critérios definidos para cada atividade."),
        (1563995880007139428, "Abyssus", "Acompanhamento operacional", "Acompanha o andamento das missões, identifica pendências e comunica necessidades de intervenção."),
        (1563995880007139427, "Apocalypse", "Controle de resultados", "Auxilia na conferência dos resultados e na consistência dos registros das operações."),
        (1563995880007139426, "Perdition", "Suporte estratégico", "Presta apoio às demandas do núcleo e contribui para a execução organizada das responsabilidades do OCTÓGONO."),
    )
    linhas = [
        "## 𓂀 NÊMESIS • HIERARQUIA OCTÓGONO",
        "Núcleo exclusivo responsável pela gestão de missões e pela supervisão das operações atribuídas ao OCTÓGONO.",
        "",
        "**OS OITO CARGOS • FUNÇÕES E RESPONSABILIDADES**",
        "",
    ]
    for numero, (cargo_id, nome, funcao, descricao) in enumerate(cargos, 1):
        linhas.extend([
            f"**{numero:02d} • {_cargo_por_nome(guild, nome, cargo_id)}**",
            f"**Função:** {funcao}.",
            f"**Descrição:** {descricao}",
            "",
            "━━━━━━━━━━━━━━━━━━━━",
            "",
        ])
    linhas.extend([
        "**ATRIBUIÇÕES DO OCTÓGONO**",
        "• Gerenciar missões, contribuições e operações especiais.",
        "• Analisar provas e validar resultados das atividades sob sua responsabilidade.",
        "• Acompanhar a execução das operações e a aplicação das recompensas.",
        "• Manter registros e decisões fundamentadas.",
        "",
        "**LIMITE DE AUTORIDADE**",
        "As atribuições específicas acima organizam a atuação interna. Não alteram automaticamente permissões individuais nem a autoridade administrativa geral da Staff.",
        "",
        "-# Esta apresentação descreve funções; permissões são definidas separadamente pela configuração do servidor.",
        "-# NÊMESIS — Authority Beyond Rank.",
    ])
    return _limitar("\n".join(linhas), limite=3900)

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
