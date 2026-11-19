from __future__ import annotations

import asyncio
import logging
import time
import uuid

import discord
from discord.ext import commands

from cogs.progressao_gangue import CARGO_NEMESIS_ID
from utils.apresentacao import criar_embed
from utils.guild_config import GUILD_NEMESIS_ID, membro_tem_lideranca
from utils.storage import atualizar_json, carregar

log = logging.getLogger(__name__)
CANAL_REPUTACAO_ID = 1563995881315897551
ARQUIVO = "reputacao_individual_nemesis.json"
COR = 0x8B1E2D
CATEGORIAS = ("Lealdade", "Disciplina", "Contribuição", "Liderança", "Mérito operacional", "Espírito de equipe")
PONTOS = (1, 2, 3, 5)
COOLDOWN = 86400


def elegivel(membro):
    return bool(isinstance(membro, discord.Member) and membro.guild.id == GUILD_NEMESIS_ID
                and any(role.id == CARGO_NEMESIS_ID for role in membro.roles))


def inteiro(valor):
    try:
        return int(valor or 0)
    except (TypeError, ValueError, OverflowError):
        return 0


async def ler(guild_id):
    bruto = await carregar(ARQUIVO, {})
    dados = bruto.get(str(guild_id), {}) if isinstance(bruto, dict) else {}
    return dados if isinstance(dados, dict) else {}


async def alterar(guild_id, funcao):
    chave = str(guild_id)
    def aplicar(bruto):
        if not isinstance(bruto, dict):
            bruto = {}
        dados = bruto.get(chave, {})
        if not isinstance(dados, dict):
            dados = {}
        funcao(dados)
        bruto[chave] = dados
        return bruto
    resultado = await atualizar_json(ARQUIVO, {}, aplicar)
    return resultado.get(chave, {})


def perfil_embed(guild, membro, perfil):
    historico = [item for item in perfil.get("historico", []) if isinstance(item, dict)]
    recentes = sorted(historico, key=lambda x: inteiro(x.get("timestamp")), reverse=True)[:5]
    linhas = []
    for item in recentes:
        valor = inteiro(item.get("pontos"))
        linhas.append(
            f"{'＋' if valor >= 0 else '－'} **{valor:+d}** · {discord.utils.escape_markdown(str(item.get('categoria') or 'Registro'))}\n"
            f"{discord.utils.escape_markdown(str(item.get('motivo') or 'Sem justificativa'))[:120]} · <t:{inteiro(item.get('timestamp'))}:d>"
        )
    embed = criar_embed(
        "NÊMESIS  /  DOSSIÊ DE REPUTAÇÃO",
        f"**Integrante:** {membro.mention}\n"
        f"**Reputação:** **{inteiro(perfil.get('pontos'))} pontos**\n"
        f"**Reconhecimentos aprovados:** {inteiro(perfil.get('aprovacoes'))}\n"
        f"**Registros no histórico:** {len(historico)}\n\n"
        "A reputação representa confiança, conduta e contribuição reconhecidas pela organização.",
        cor=COR, rodape="NÊMESIS • REPUTAÇÃO INDIVIDUAL • Histórico auditável",
    )
    embed.add_field(name="HISTÓRICO RECENTE", value="\n\n".join(linhas) if linhas else "Nenhum reconhecimento registrado.", inline=False)
    return embed


class MotivoModal(discord.ui.Modal, title="Indicação de reconhecimento"):
    motivo = discord.ui.TextInput(
        label="Justificativa do reconhecimento",
        style=discord.TextStyle.paragraph, min_length=20, max_length=500,
        placeholder="Descreva a atitude, contribuição ou mérito observado.",
    )

    def __init__(self, cog, autor_id, alvo_id, categoria):
        super().__init__(timeout=300)
        self.cog, self.autor_id, self.alvo_id, self.categoria = cog, autor_id, alvo_id, categoria

    async def on_submit(self, interaction):
        await interaction.response.defer(ephemeral=True, thinking=True)
        try:
            protocolo = await self.cog.criar_indicacao(
                interaction.guild, self.autor_id, self.alvo_id, self.categoria, str(self.motivo.value)
            )
        except ValueError as erro:
            await interaction.followup.send(str(erro), ephemeral=True)
            return
        await interaction.followup.send(
            f"Indicação registrada: **{protocolo}**. A liderança precisa analisá-la; nenhum ponto foi concedido ainda.",
            ephemeral=True,
        )


class CategoriaSelect(discord.ui.Select):
    def __init__(self, cog, autor_id, alvo_id):
        self.cog, self.autor_id, self.alvo_id = cog, autor_id, alvo_id
        super().__init__(
            placeholder="Selecione a categoria",
            options=[discord.SelectOption(label=nome, value=nome) for nome in CATEGORIAS],
            min_values=1, max_values=1,
        )

    async def callback(self, interaction):
        if interaction.user.id != self.autor_id:
            await interaction.response.send_message("Esta indicação pertence a outro membro.", ephemeral=True)
            return
        await interaction.response.send_modal(MotivoModal(self.cog, self.autor_id, self.alvo_id, self.values[0]))


class CategoriaView(discord.ui.View):
    def __init__(self, cog, autor_id, alvo_id):
        super().__init__(timeout=300)
        self.add_item(CategoriaSelect(cog, autor_id, alvo_id))


class AlvoView(discord.ui.View):
    def __init__(self, cog, autor_id):
        super().__init__(timeout=300)
        self.cog, self.autor_id = cog, autor_id
        seletor = discord.ui.UserSelect(placeholder="Escolha o integrante que deseja indicar", min_values=1, max_values=1)
        seletor.callback = self.selecionar
        self.add_item(seletor)

    async def selecionar(self, interaction):
        if interaction.user.id != self.autor_id:
            await interaction.response.send_message("Esta indicação pertence a outro membro.", ephemeral=True)
            return
        alvo = self.children[0].values[0]
        if alvo.id == self.autor_id:
            await interaction.response.send_message("Você não pode indicar a si mesmo.", ephemeral=True)
            return
        if not elegivel(alvo):
            await interaction.response.send_message("O indicado precisa possuir o cargo oficial NÊMESIS.", ephemeral=True)
            return
        await interaction.response.send_message(
            "Escolha o critério do reconhecimento.", view=CategoriaView(self.cog, self.autor_id, alvo.id), ephemeral=True
        )


def _layout_reputacao(origem: discord.ui.View, texto: str, rodape: str):
    """Converte os controles do sistema em um cartão Components V2."""
    componentes = [
        discord.ui.TextDisplay(texto[:3900]),
        discord.ui.Separator(visible=True, spacing=discord.SeparatorSpacing.small),
    ]
    for item in origem.children:
        if isinstance(item, discord.ui.Select):
            seletor = discord.ui.Select(
                placeholder=item.placeholder,
                options=item.options,
                custom_id=item.custom_id,
                min_values=item.min_values,
                max_values=item.max_values,
                disabled=item.disabled,
            )
            seletor.callback = item.callback
            componentes.append(discord.ui.ActionRow(seletor))
        elif isinstance(item, discord.ui.Button):
            botao = discord.ui.Button(
                label=item.label, style=item.style, disabled=item.disabled,
                custom_id=item.custom_id, url=item.url, emoji=item.emoji,
            )
            botao.callback = item.callback
            componentes.append(discord.ui.ActionRow(botao))
    componentes.extend([
        discord.ui.Separator(visible=True, spacing=discord.SeparatorSpacing.small),
        discord.ui.TextDisplay(f"-# {rodape}"),
    ])
    return discord.ui.Container(*componentes, accent_colour=COR)


class RevisaoLayoutView(discord.ui.LayoutView):
    def __init__(self, cog, protocolo, texto):
        super().__init__(timeout=None)
        origem = RevisaoView(cog, protocolo)
        self.add_item(_layout_reputacao(origem, texto, "NÊMESIS • REPUTAÇÃO • Análise da liderança"))


class PainelLayoutView(discord.ui.LayoutView):
    def __init__(self, cog, texto):
        super().__init__(timeout=None)
        origem = PainelView(cog)
        self.add_item(_layout_reputacao(origem, texto, "NÊMESIS • REPUTAÇÃO INDIVIDUAL"))


class RevisaoView(discord.ui.View):
    def __init__(self, cog, protocolo):
        super().__init__(timeout=None)
        self.cog, self.protocolo = cog, protocolo
        self.add_item(discord.ui.Select(
            placeholder="Selecione a decisão da liderança",
            custom_id="nemesis:reputacao:revisao",
            min_values=1, max_values=1,
            options=[
                discord.SelectOption(label="Aprovar · +1 ponto", value="1", description="Reconhecimento básico"),
                discord.SelectOption(label="Aprovar · +2 pontos", value="2", description="Reconhecimento relevante"),
                discord.SelectOption(label="Aprovar · +3 pontos", value="3", description="Reconhecimento expressivo"),
                discord.SelectOption(label="Aprovar · +5 pontos", value="5", description="Mérito excepcional"),
                discord.SelectOption(label="Rejeitar indicação", value="rejeitar", description="Não conceder reputação"),
            ],
        ))
        self.children[0].callback = self.selecionar

    async def selecionar(self, interaction):
        if not membro_tem_lideranca(interaction.user):
            await interaction.response.send_message("Apenas a liderança pode analisar indicações.", ephemeral=True)
            return
        valor = self.children[0].values[0]
        pontos = None if valor == "rejeitar" else int(valor)
        try:
            await self.cog.decidir(interaction.guild, self.protocolo, interaction.user.id, pontos)
        except ValueError as erro:
            await interaction.response.send_message(str(erro), ephemeral=True)
            return
        await interaction.response.send_message(
            f"Indicação {self.protocolo}: " + (f"aprovada com +{pontos} pontos." if pontos else "rejeitada."),
            ephemeral=True,
        )
        try:
            await interaction.message.edit(
                content=None, embeds=[], attachments=[],
                view=RevisaoLayoutView(
                    self.cog, self.protocolo,
                    _texto_revisao(self.protocolo, self.cog, pontos, "aprovada" if pontos else "rejeitada"),
                ),
            )
        except discord.HTTPException:
            log.exception("Não foi possível atualizar o cartão da indicação %s.", self.protocolo)


class PainelView(discord.ui.View):
    def __init__(self, cog):
        super().__init__(timeout=None)
        self.cog = cog
        seletor = discord.ui.Select(
            placeholder="Escolha uma opção de reputação",
            custom_id="nemesis:reputacao:acoes",
            min_values=1, max_values=1,
            options=[
                discord.SelectOption(label="Minha reputação", value="perfil", description="Consultar seu dossiê individual"),
                discord.SelectOption(label="Indicar integrante", value="indicar", description="Enviar reconhecimento para análise"),
                discord.SelectOption(label="Ranking", value="ranking", description="Consultar os integrantes mais reconhecidos"),
                discord.SelectOption(label="Analisar indicações", value="analisar", description="Área restrita à liderança"),
            ],
        )
        seletor.callback = self.selecionar
        self.add_item(seletor)

    async def selecionar(self, interaction):
        acao = self.children[0].values[0]
        if acao in ("perfil", "indicar", "ranking") and not elegivel(interaction.user):
            await interaction.response.send_message(
                "Este recurso é exclusivo de integrantes com o cargo oficial NÊMESIS.", ephemeral=True
            )
            return
        if acao == "perfil":
            dados = await ler(interaction.guild.id)
            membro = dados.get("membros", {}).get(str(interaction.user.id), {})
            await interaction.response.send_message(
                embed=perfil_embed(interaction.guild, interaction.user, membro), ephemeral=True
            )
            return
        if acao == "indicar":
            await interaction.response.send_message(
                "Selecione quem deseja indicar.",
                view=AlvoView(self.cog, interaction.user.id), ephemeral=True
            )
            return
        if acao == "ranking":
            dados = await ler(interaction.guild.id)
            membros = dados.get("membros", {})
            lista = []
            for uid, item in membros.items():
                membro = interaction.guild.get_member(inteiro(uid))
                if membro and elegivel(membro):
                    lista.append((membro, inteiro(item.get("pontos"))))
            lista.sort(key=lambda item: item[1], reverse=True)
            linhas = [
                f"{('🥇','🥈','🥉')[i] if i < 3 else f'#{i+1}'}  {membro.mention} — **{pontos} pontos**"
                for i, (membro, pontos) in enumerate(lista[:10]) if pontos > 0
            ]
            embed = criar_embed(
                "NÊMESIS  /  QUADRO DE REPUTAÇÃO",
                "\\n".join(linhas) if linhas else "O ranking ainda não possui pontuações.",
                cor=COR, rodape="NÊMESIS • MÉRITO INDIVIDUAL • Atualização em tempo real",
            )
            await interaction.response.send_message(embed=embed, ephemeral=True)
            return
        if acao == "analisar":
            if not membro_tem_lideranca(interaction.user):
                await interaction.response.send_message("Área restrita à liderança.", ephemeral=True)
                return
            dados = await ler(interaction.guild.id)
            pendentes = [
                item for item in dados.get("indicacoes", {}).values()
                if isinstance(item, dict) and item.get("status") == "pendente"
            ]
            pendentes.sort(key=lambda item: inteiro(item.get("criado_em")))
            if not pendentes:
                await interaction.response.send_message("Não existem indicações pendentes.", ephemeral=True)
                return
            await interaction.response.send_message(
                f"Há **{len(pendentes)}** indicações pendentes. Consulte as publicações de análise neste canal.",
                ephemeral=True,
            )


def _componentes_contem_marcador(componentes, marcador):
    pendentes = list(componentes or [])
    while pendentes:
        componente = pendentes.pop()
        if marcador in str(getattr(componente, "content", "") or ""):
            return True
        pendentes.extend(list(getattr(componente, "children", []) or []))
    return False


def _texto_painel(embed):
    partes = [f"## {embed.title or 'NÊMESIS / SISTEMA DE REPUTAÇÃO'}"]
    if embed.description:
        partes.append(embed.description)
    for campo in embed.fields:
        partes.append(f"**{campo.name}**\n{campo.value}")
    if embed.footer and embed.footer.text:
        partes.append(f"-# {embed.footer.text}")
    return "\n\n".join(partes)


def _texto_revisao(protocolo, cog, pontos=None, status="pendente"):
    if status == "pendente":
        detalhe = "A liderança deve selecionar a pontuação ou rejeitar a indicação no menu abaixo."
    elif status == "aprovada":
        detalhe = f"Indicação aprovada. Pontuação concedida: **+{pontos} pontos**."
    else:
        detalhe = "Indicação rejeitada. Nenhum ponto foi concedido."
    return (
        "## NÊMESIS / INDICAÇÃO EM ANÁLISE\n"
        f"**Protocolo:** {protocolo}\n"
        f"**Estado:** {status.capitalize()}\n"
        f"{detalhe}"
    )


class Reputacao(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self._lock = asyncio.Lock()
        self._sincronizado = False

    async def criar_indicacao(self, guild, autor_id, alvo_id, categoria, motivo):
        if guild is None or guild.id != GUILD_NEMESIS_ID:
            raise ValueError("Sistema exclusivo da NÊMESIS.")
        autor, alvo = guild.get_member(autor_id), guild.get_member(alvo_id)
        if not elegivel(autor) or not elegivel(alvo):
            raise ValueError("Autor e indicado precisam possuir o cargo oficial NÊMESIS.")
        if autor_id == alvo_id:
            raise ValueError("Autoindicação não é permitida.")
        if categoria not in CATEGORIAS or len(motivo.strip()) < 20:
            raise ValueError("Informe uma categoria válida e uma justificativa de pelo menos 20 caracteres.")
        protocolo, agora = uuid.uuid4().hex[:8].upper(), int(time.time())
        def aplicar(dados):
            indicacoes = dados.setdefault("indicacoes", {})
            cooldowns = dados.setdefault("cooldowns", {})
            if agora - inteiro(cooldowns.get(str(autor_id))) < COOLDOWN:
                raise ValueError("Você já enviou uma indicação nas últimas 24 horas.")
            if any(x.get("status") == "pendente" and inteiro(x.get("autor_id")) == autor_id
                   and inteiro(x.get("alvo_id")) == alvo_id for x in indicacoes.values() if isinstance(x, dict)):
                raise ValueError("Já existe uma indicação sua pendente para esse integrante.")
            indicacoes[protocolo] = {
                "protocolo": protocolo, "autor_id": autor_id, "alvo_id": alvo_id,
                "categoria": categoria, "motivo": motivo.strip(), "status": "pendente",
                "criado_em": agora, "pontos": 0, "decisor_id": None,
            }
            cooldowns[str(autor_id)] = agora
        await alterar(guild.id, aplicar)
        canal = guild.get_channel(CANAL_REPUTACAO_ID)
        if isinstance(canal, discord.TextChannel):
            embed = criar_embed(
                "NÊMESIS  /  INDICAÇÃO EM ANÁLISE",
                f"**Protocolo:** {protocolo}\n**Integrante indicado:** <@{alvo_id}>\n"
                f"**Indicação enviada por:** <@{autor_id}>\n**Categoria:** {categoria}\n\n"
                f"**Justificativa**\n{discord.utils.escape_markdown(motivo)}\n\n"
                "**Estado:** aguardando decisão da liderança. Nenhum ponto foi concedido.",
                cor=COR, rodape="NÊMESIS • REPUTAÇÃO • Registro de mérito",
            )
            mensagem = await canal.send(view=RevisaoLayoutView(self, protocolo, (
                f"## NÊMESIS / INDICAÇÃO EM ANÁLISE\n**Protocolo:** {protocolo}\n"
                f"**Integrante indicado:** <@{alvo_id}>\n**Indicação enviada por:** <@{autor_id}>\n"
                f"**Categoria:** {categoria}\n\n**Justificativa**\n{discord.utils.escape_markdown(motivo)}\n\n"
                "**Estado:** aguardando decisão da liderança. Nenhum ponto foi concedido."
            )))
            def guardar_mensagem(dados):
                item = dados.setdefault("indicacoes", {}).get(protocolo)
                if isinstance(item, dict):
                    item["mensagem_id"] = mensagem.id
            await alterar(guild.id, guardar_mensagem)
        return protocolo

    async def decidir(self, guild, protocolo, decisor_id, pontos):
        decisor = guild.get_member(decisor_id) if guild else None
        if not membro_tem_lideranca(decisor):
            raise ValueError("Apenas a liderança pode decidir.")
        if pontos is not None and pontos not in PONTOS:
            raise ValueError("Pontuação inválida.")
        agora = int(time.time())
        def aplicar(dados):
            indicacoes = dados.setdefault("indicacoes", {})
            item = indicacoes.get(protocolo)
            if not isinstance(item, dict) or item.get("status") != "pendente":
                raise ValueError("Indicação inexistente ou já analisada.")
            if inteiro(item.get("autor_id")) == decisor_id:
                raise ValueError("Você não pode aprovar a própria indicação.")
            alvo = guild.get_member(inteiro(item.get("alvo_id")))
            if not elegivel(alvo):
                raise ValueError("O indicado não possui mais o cargo NÊMESIS; indicação não pode ser aprovada.")
            item.update({
                "status": "aprovada" if pontos else "rejeitada",
                "pontos": inteiro(pontos), "decisor_id": decisor_id, "decidido_em": agora,
            })
            if pontos:
                membros = dados.setdefault("membros", {})
                perfil = membros.setdefault(str(alvo.id), {"pontos": 0, "aprovacoes": 0, "historico": []})
                perfil["pontos"] = max(0, inteiro(perfil.get("pontos"))) + pontos
                perfil["aprovacoes"] = inteiro(perfil.get("aprovacoes")) + 1
                historico = perfil.setdefault("historico", [])
                historico.append({
                    "protocolo": protocolo, "pontos": pontos, "categoria": item.get("categoria"),
                    "motivo": item.get("motivo"), "autor_id": item.get("autor_id"),
                    "decisor_id": decisor_id, "timestamp": agora,
                })
                perfil["historico"] = historico[-1000:]
            indicacoes[protocolo] = item
        await alterar(guild.id, aplicar)

    @commands.Cog.listener()
    async def on_ready(self):
        if self._sincronizado:
            return
        canal = self.bot.get_channel(CANAL_REPUTACAO_ID)
        if canal is None:
            try:
                canal = await self.bot.fetch_channel(CANAL_REPUTACAO_ID)
            except (discord.NotFound, discord.Forbidden, discord.HTTPException):
                log.exception("Canal de reputação indisponível (%s).", CANAL_REPUTACAO_ID)
                return
        if not isinstance(canal, discord.TextChannel):
            log.error("Canal de reputação não é um canal de texto: %s", CANAL_REPUTACAO_ID)
            return
        dados_pendentes = await ler(GUILD_NEMESIS_ID)
        for protocolo, item in dados_pendentes.get("indicacoes", {}).items():
            if isinstance(item, dict) and item.get("status") == "pendente" and item.get("mensagem_id"):
                self.bot.add_view(
                    RevisaoLayoutView(self, protocolo, _texto_revisao(protocolo, self)),
                    message_id=inteiro(item.get("mensagem_id")),
                )
        embed = criar_embed(
            "NÊMESIS  /  SISTEMA DE REPUTAÇÃO",
            "A reputação registra o mérito individual, a confiança e a contribuição de cada integrante.\n\n"
            "**COMO FUNCIONA**\n"
            "• Integrantes com o cargo oficial NÊMESIS podem indicar outro membro.\n"
            "• Toda indicação exige categoria e justificativa objetiva.\n"
            "• A liderança avalia e concede **+1, +2, +3 ou +5 pontos**, ou rejeita.\n"
            "• Cada membro pode enviar uma indicação a cada 24 horas.\n\n"
            "**CRITÉRIOS**\n"
            "Lealdade · Disciplina · Contribuição · Liderança · Mérito operacional · Espírito de equipe\n\n"
            "**INTEGRIDADE**\n"
            "Autoindicação e acordos de troca são proibidos. A reputação não é moeda, não substitui XP, "
            "não promove cargos e não concede permissões.",
            cor=COR, rodape="NÊMESIS • AUTHORITY BEYOND RANK • Reputação individual",
        )
        embed.set_thumbnail(url=self.bot.user.display_avatar.url)
        self.bot.add_view(PainelLayoutView(self, _texto_painel(embed)))
        existentes = []
        async for mensagem in canal.history(limit=None, oldest_first=True):
            if mensagem.author.id != self.bot.user.id:
                continue
            componentes_v2 = _componentes_contem_marcador(
                mensagem.components, "NÊMESIS • REPUTAÇÃO INDIVIDUAL"
            )
            embed_legado = False
            if mensagem.embeds:
                primeiro = mensagem.embeds[0]
                titulo = primeiro.title or ""
                rodape = primeiro.footer.text or "" if primeiro.footer else ""
                embed_legado = (
                    titulo == "NÊMESIS  /  SISTEMA DE REPUTAÇÃO"
                    or "REPUTAÇÃO INDIVIDUAL" in rodape
                )
            if componentes_v2 or embed_legado:
                existentes.append(mensagem)

        if existentes:
            canonica = existentes[0]
            await canonica.edit(
                content=None, embeds=[], attachments=[],
                view=PainelLayoutView(self, _texto_painel(embed)),
            )
            removidas = 0
            for duplicada in existentes[1:]:
                try:
                    await duplicada.delete()
                    removidas += 1
                except discord.HTTPException:
                    log.exception("Não foi possível remover painel duplicado de reputação (%s).", duplicada.id)
            log.info(
                "Painel de reputação deduplicado (canal=%s, mensagem=%s, cópias_removidas=%s).",
                canal.id, canonica.id, removidas,
            )
        else:
            mensagem = await canal.send(view=PainelLayoutView(self, _texto_painel(embed)))
            log.info("Painel de reputação publicado (canal=%s, mensagem=%s).", canal.id, mensagem.id)
        self._sincronizado = True
        log.info("Sincronização do sistema de reputação concluída.")


async def setup(bot):
    await bot.add_cog(Reputacao(bot))
