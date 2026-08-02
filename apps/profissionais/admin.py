from django.contrib import admin
from django.urls import reverse
from django.utils.html import format_html

from .models import Profissional


@admin.register(Profissional)
class ProfissionalAdmin(admin.ModelAdmin):

    list_display = (
        "nome",
        "usuario",
        "cidade",
        "categoria",
        "empresa",
        "especialidade",
        "destaque",
        "ativo",
        "ver_metricas",
    )

    list_filter = (
        "cidade",
        "categoria",
        "empresa",
        "destaque",
        "ativo",
        "atendimento_domiciliar",
    )

    search_fields = (
        "nome",
        "especialidade",
        "descricao",
        "telefone",
        "whatsapp",
        "email",
        "usuario__username",
        "usuario__email",
    )

    autocomplete_fields = (
        "usuario",
        "cidade",
        "categoria",
        "empresa",
    )

    prepopulated_fields = {
        "slug": ("nome",)
    }

    list_per_page = 30

    readonly_fields = (
        "painel_metricas",
        "liberacao_financeira_por",
        "liberacao_financeira_em",
    )

    fieldsets = (

        (
            "Identificação",
            {
                "fields": (
                    "nome",
                    "slug",
                    "foto",
                    "categoria",
                    "empresa",
                    "cidade",
                )
            },
        ),

        (
            "Responsável pelo acesso",
            {
                "description": (
                    "Usuário autorizado a acessar a área "
                    "deste profissional no Portal do Cliente."
                ),
                "fields": (
                    "usuario",
                ),
            },
        ),

        (
            "Apresentação",
            {
                "fields": (
                    "especialidade",
                    "descricao",
                )
            },
        ),

        (
            "Contato",
            {
                "fields": (
                    "telefone",
                    "whatsapp",
                    "email",
                    "instagram",
                    "site",
                )
            },
        ),

        (
            "Localização",
            {
                "fields": (
                    "endereco",
                    "bairro",
                    "horario",
                )
            },
        ),

        (
            "Configurações",
            {
                "fields": (
                    "atendimento_domiciliar",
                    "destaque",
                    "ativo",
                )
            },
        ),

        (
            "Métricas",
            {
                "fields": (
                    "painel_metricas",
                )
            },
        ),

        (
            "Liberação financeira",
            {
                "fields": (
                    "liberacao_financeira_ativa", "liberacao_financeira_ate",
                    "liberacao_financeira_motivo", "liberacao_financeira_observacao",
                    "liberacao_financeira_por", "liberacao_financeira_em",
                )
            },
        ),

    )

    @admin.display(description="Métricas")
    def ver_metricas(self, obj):

        if not obj.pk:
            return "-"

        url = reverse(
            "metricas:painel_profissional",
            args=[obj.pk],
        )

        return format_html(
            '<a href="{}">📊 Ver métricas</a>',
            url,
        )

    @admin.display(
        description="Painel de desempenho"
    )
    def painel_metricas(self, obj):

        if not obj or not obj.pk:
            return (
                "Salve o profissional para "
                "habilitar o painel de métricas."
            )

        url = reverse(
            "metricas:painel_profissional",
            args=[obj.pk],
        )

        return format_html(
            '<a class="button" href="{}">'
            '📊 Abrir painel de métricas'
            '</a>',
            url,
        )
