from django.urls import path

from . import views

app_name = "empresas"

urlpatterns = [

    path(
        "",
        views.listar_empresas,
        name="listar",
    ),

    path(
        "<int:pk>/",
        views.visualizar_empresa,
        name="visualizar",
    ),

    path(
        "<int:pk>/editar/",
        views.editar_empresa,
        name="editar",
    ),

]