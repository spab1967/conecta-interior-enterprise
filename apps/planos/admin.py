from django.contrib import admin, messages
from django.utils import timezone

from .models import Assinatura, Plano
from .vigencia import adicionar_um_mes


@admin.register(Plano)
class PlanoAdmin(admin.ModelAdmin):

    list_display = (
        "nome",
        "preco_mensal",
        "acesso_metricas",
        "destaque_busca",
        "destaque_perfil",
        "prioridade_resultados",
        "selo_destaque",
        "limite_fotos",
        "ativo",
        "ordem",
    )

    list_filter = (
        "ativo",
        "acesso_metricas",
        "destaque_busca",
        "destaque_perfil",
        "prioridade_resultados",
        "selo_destaque",
    )

    search_fields = (
        "nome",
        "descricao",
    )

    ordering = (
        "ordem",
        "preco_mensal",
    )

    list_editable = (
        "ativo",
        "ordem",
    )

    fieldsets = (

        (
            "Plano",
            {
                "fields": (
                    "nome",
                    "descricao",
                    "preco_mensal",
                    "ativo",
                    "ordem",
                )
            },
        ),

        (
            "Benefícios",
            {
                "fields": (
                    "destaque_busca",
                    "destaque_perfil",
                    "acesso_metricas",
                    "prioridade_resultados",
                    "selo_destaque",
                    "limite_fotos",
                )
            },
        ),

    )


@admin.register(Assinatura)
class AssinaturaAdmin(admin.ModelAdmin):

    list_display = (
        "titular",
        "tipo_titular",
        "plano",
        "status",
        "inicio",
        "vencimento",
        "situacao",
        "dias_restantes",
        "renovacao_automatica",
    )

    list_filter = (
        "status",
        "plano",
        "renovacao_automatica",
        "inicio",
        "vencimento",
    )

    search_fields = (
        "empresa__nome_fantasia",
        "profissional__nome",
        "plano__nome",
    )

    autocomplete_fields = (
        "empresa",
        "profissional",
        "plano",
    )

    date_hierarchy = "inicio"

    list_per_page = 50

    actions = (
        "renovar_por_um_mes",
        "ativar_assinaturas",
        "cancelar_assinaturas",
        "marcar_como_pendentes",
        "marcar_como_vencidas",
    )

    fieldsets = (

        (
            "Titular",
            {
                "description":
                    "Preencha somente Empresa ou Profissional.",
                "fields": (
                    "empresa",
                    "profissional",
                ),
            },
        ),

        (
            "Plano contratado",
            {
                "fields": (
                    "plano",
                    "status",
                ),
            },
        ),

        (
            "Vigência",
            {
                "fields": (
                    "inicio",
                    "vencimento",
                    "renovacao_automatica",
                ),
            },
        ),

        (
            "Controle administrativo",
            {
                "fields": (
                    "observacoes",
                ),
            },
        ),

    )

    @admin.display(
        description="Situação",
        ordering="vencimento",
    )
    def situacao(self, obj):

        hoje = timezone.localdate()

        if obj.status == Assinatura.STATUS_CANCELADA:
            return "Cancelada"

        if obj.status == Assinatura.STATUS_PENDENTE:
            return "Pendente"

        if obj.status == Assinatura.STATUS_VENCIDA:
            return "Vencida"

        if obj.status != Assinatura.STATUS_ATIVA:
            return obj.get_status_display()

        if not obj.vencimento:
            return "Vigente — sem vencimento"

        dias = (
            obj.vencimento - hoje
        ).days

        if dias < 0:
            return "Vencida"

        if dias == 0:
            return "Vence hoje"

        if dias <= 7:
            return "Próxima do vencimento"

        return "Vigente"

    @admin.display(
        description="Dias restantes",
        ordering="vencimento",
    )
    def dias_restantes(self, obj):

        if obj.status != Assinatura.STATUS_ATIVA:
            return "-"

        if not obj.vencimento:
            return "Sem vencimento"

        hoje = timezone.localdate()

        dias = (
            obj.vencimento - hoje
        ).days

        if dias < 0:
            return "Vencida"

        if dias == 0:
            return "Vence hoje"

        if dias == 1:
            return "1 dia"

        return f"{dias} dias"

    @admin.action(
        description="Renovar selecionadas por 1 mês"
    )
    def renovar_por_um_mes(
        self,
        request,
        queryset,
    ):

        hoje = timezone.localdate()

        renovadas = 0
        gratuitas = 0
        erros = 0

        for assinatura in queryset.select_related(
            "plano"
        ):

            try:

                if assinatura.plano.preco_mensal <= 0:

                    assinatura.status = (
                        Assinatura.STATUS_ATIVA
                    )

                    assinatura.vencimento = None

                    assinatura.save(
                        update_fields=[
                            "status",
                            "vencimento",
                            "atualizada_em",
                        ]
                    )

                    gratuitas += 1
                    continue

                if (
                    assinatura.vencimento
                    and assinatura.vencimento >= hoje
                ):

                    data_base = assinatura.vencimento

                else:

                    data_base = hoje

                novo_vencimento = adicionar_um_mes(
                    data_base
                )

                assinatura.status = (
                    Assinatura.STATUS_ATIVA
                )

                assinatura.vencimento = novo_vencimento

                assinatura.save(
                    update_fields=[
                        "status",
                        "vencimento",
                        "atualizada_em",
                    ]
                )

                renovadas += 1

            except Exception as erro:

                erros += 1

                self.message_user(
                    request,
                    (
                        f"Erro ao renovar "
                        f"'{assinatura.titular}': {erro}"
                    ),
                    level=messages.ERROR,
                )

        if renovadas:

            self.message_user(
                request,
                (
                    f"{renovadas} assinatura(s) "
                    f"renovada(s) por 1 mês."
                ),
                level=messages.SUCCESS,
            )

        if gratuitas:

            self.message_user(
                request,
                (
                    f"{gratuitas} assinatura(s) gratuita(s) "
                    f"mantida(s) ativa(s) sem vencimento."
                ),
                level=messages.SUCCESS,
            )

        if erros:

            self.message_user(
                request,
                (
                    f"{erros} assinatura(s) "
                    f"não puderam ser renovadas."
                ),
                level=messages.ERROR,
            )

    @admin.action(
        description="Ativar assinaturas selecionadas"
    )
    def ativar_assinaturas(
        self,
        request,
        queryset,
    ):

        total = queryset.update(
            status=Assinatura.STATUS_ATIVA
        )

        self.message_user(
            request,
            f"{total} assinatura(s) ativada(s).",
        )

    @admin.action(
        description="Cancelar assinaturas selecionadas"
    )
    def cancelar_assinaturas(
        self,
        request,
        queryset,
    ):

        total = queryset.update(
            status=Assinatura.STATUS_CANCELADA
        )

        self.message_user(
            request,
            f"{total} assinatura(s) cancelada(s).",
        )

    @admin.action(
        description="Marcar selecionadas como pendentes"
    )
    def marcar_como_pendentes(
        self,
        request,
        queryset,
    ):

        total = queryset.update(
            status=Assinatura.STATUS_PENDENTE
        )

        self.message_user(
            request,
            (
                f"{total} assinatura(s) "
                f"marcada(s) como pendente(s)."
            ),
        )

    @admin.action(
        description="Marcar selecionadas como vencidas"
    )
    def marcar_como_vencidas(
        self,
        request,
        queryset,
    ):

        total = queryset.update(
            status=Assinatura.STATUS_VENCIDA
        )

        self.message_user(
            request,
            (
                f"{total} assinatura(s) "
                f"marcada(s) como vencida(s)."
            ),
        )