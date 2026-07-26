from django.contrib import admin

from .models import Avaliacao


@admin.register(Avaliacao)
class AvaliacaoAdmin(admin.ModelAdmin):

    list_display = (
        "id",
        "empresa",
        "profissional",
        "nome",
        "nota",
        "aprovado",
        "criado_em",
    )

    list_filter = (
        "nota",
        "aprovado",
    )

    search_fields = (
        "nome",
        "comentario",
    )

    ordering = (
        "-criado_em",
    )