from django.urls import path

from . import views


app_name = "avaliacoes"


urlpatterns = [

    path(
        "empresa/<slug:cidade_slug>/<slug:empresa_slug>/",
        views.avaliar_empresa,
        name="avaliar_empresa",
    ),

    path(
        "profissional/<slug:cidade_slug>/<slug:profissional_slug>/",
        views.avaliar_profissional,
        name="avaliar_profissional",
    ),

    path(
        "sucesso/",
        views.sucesso,
        name="sucesso",
    ),

]