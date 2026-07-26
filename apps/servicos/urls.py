from django.urls import path

from . import views

app_name = "servicos"

urlpatterns = [
    path(
        "empresa/<int:empresa_id>/",
        views.gerenciar_empresa,
        name="gerenciar_empresa",
    ),
    path(
        "profissional/<int:profissional_id>/",
        views.gerenciar_profissional,
        name="gerenciar_profissional",
    ),
    path(
        "<int:servico_id>/editar/",
        views.editar,
        name="editar",
    ),
    path(
        "<int:servico_id>/alternar-ativo/",
        views.alternar_ativo,
        name="alternar_ativo",
    ),
    path(
        "<int:servico_id>/excluir/",
        views.excluir,
        name="excluir",
    ),
]
