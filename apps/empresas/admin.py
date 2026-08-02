from django.contrib import admin
from django.urls import reverse
from django.utils.html import format_html

from .models import Empresa


@admin.register(Empresa)
class EmpresaAdmin(admin.ModelAdmin):

    list_display = (
        "nome_fantasia",
        "usuario",
        "cidade",
        "categoria",
        "destaque",
        "ativa",
        "ver_metricas",
    )

    list_filter = (
        "cidade",
        "categoria",
        "destaque",
        "ativa",
    )

    search_fields = (
        "nome_fantasia",
        "descricao",
        "telefone",
        "whatsapp",
        "email",
        "usuario__username",
        "usuario__email",
    )

    prepopulated_fields = {
        "slug": ("nome_fantasia",)
    }

    autocomplete_fields = (
        "usuario",
        "cidade",
        "categoria",
    )

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
                    "nome_fantasia",
                    "slug",
                    "logo",
                    "categoria",
                    "cidade",
                )
            },
        ),

        (
            "Responsável pelo acesso",
            {
                "description": (
                    "Usuário autorizado a acessar a área "
                    "desta empresa no Portal do Cliente."
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
                    "destaque",
                    "ativa",
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
            "metricas:painel_empresa",
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
                "Salve a empresa para habilitar "
                "o painel de métricas."
            )

        url = reverse(
            "metricas:painel_empresa",
            args=[obj.pk],
        )

        return format_html(
            '<a class="button" href="{}">'
            '📊 Abrir painel de métricas'
            '</a>',
            url,
        )
