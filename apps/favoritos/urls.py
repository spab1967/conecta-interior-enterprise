from django.urls import path

from . import views


app_name = "favoritos"


urlpatterns = [

    path(
        "",
        views.meus_favoritos,
        name="meus_favoritos",
    ),

    path(
        "empresa/<slug:cidade_slug>/<slug:empresa_slug>/",
        views.alternar_empresa,
        name="alternar_empresa",
    ),

    path(
        "profissional/<slug:cidade_slug>/<slug:profissional_slug>/",
        views.alternar_profissional,
        name="alternar_profissional",
    ),

    path(
        "remover/empresa/<slug:cidade_slug>/<slug:empresa_slug>/",
        views.remover_empresa,
        name="remover_empresa",
    ),

    path(
        "remover/profissional/<slug:cidade_slug>/<slug:profissional_slug>/",
        views.remover_profissional,
        name="remover_profissional",
    ),

]