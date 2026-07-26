from django.contrib import admin

from .models import Favorito


@admin.register(Favorito)
class FavoritoAdmin(admin.ModelAdmin):

    list_display = (
        "id",
        "identificador",
        "empresa",
        "profissional",
        "criado_em",
    )

    search_fields = (
        "identificador",
        "empresa__nome_fantasia",
        "profissional__nome",
    )

    list_filter = (
        "criado_em",
    )

    readonly_fields = (
        "criado_em",
    )

    ordering = (
        "-criado_em",
    )