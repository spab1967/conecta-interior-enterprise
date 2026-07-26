from django.contrib import admin

from .models import Cidade


@admin.register(Cidade)
class CidadeAdmin(admin.ModelAdmin):
    list_display = (
        "nome",
        "estado",
        "ddd",
        "populacao",
        "ativa",
        "atualizada_em",
    )
    list_filter = ("estado", "ativa")
    search_fields = ("nome", "cep_principal", "ddd")
    prepopulated_fields = {"slug": ("nome",)}
    readonly_fields = ("criada_em", "atualizada_em")

    fieldsets = (
        (
            "Identificação",
            {
                "fields": (
                    "nome",
                    "estado",
                    "slug",
                    "ativa",
                )
            },
        ),
        (
            "Dados municipais",
            {
                "fields": (
                    "cep_principal",
                    "ddd",
                    "populacao",
                    "latitude",
                    "longitude",
                    "telefone_util",
                    "site_prefeitura",
                )
            },
        ),
        (
            "Apresentação",
            {
                "fields": (
                    "descricao",
                    "imagem",
                    "banner",
                )
            },
        ),
        (
            "Mecanismos de busca",
            {
                "fields": (
                    "titulo_seo",
                    "descricao_seo",
                )
            },
        ),
        (
            "Controle",
            {
                "fields": (
                    "criada_em",
                    "atualizada_em",
                )
            },
        ),
    )
