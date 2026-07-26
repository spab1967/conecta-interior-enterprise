from django.urls import path

from . import views


app_name = "metricas"


urlpatterns = [

    path(
        "empresa/<int:empresa_id>/<str:tipo>/",
        views.contato_empresa,
        name="contato_empresa",
    ),

    path(
        "profissional/<int:profissional_id>/<str:tipo>/",
        views.contato_profissional,
        name="contato_profissional",
    ),

    path(
        "painel/empresa/<int:empresa_id>/",
        views.painel_empresa,
        name="painel_empresa",
    ),

    path(
        "painel/profissional/<int:profissional_id>/",
        views.painel_profissional,
        name="painel_profissional",
    ),

]