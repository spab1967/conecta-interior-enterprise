from django.contrib import admin
from .models import Categoria

@admin.register(Categoria)
class CategoriaAdmin(admin.ModelAdmin):
    list_display = ("nome", "icone", "ativa")
    list_filter = ("ativa",)
    search_fields = ("nome",)
    prepopulated_fields = {"slug": ("nome",)}
