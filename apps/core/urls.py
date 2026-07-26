from django.contrib.auth import views as auth_views
from django.urls import path

from . import views


app_name = "core"


urlpatterns = [

    path(
        "",
        views.home,
        name="home",
    ),

    path(
        "planos/",
        views.planos,
        name="planos",
    ),

    path(
        "entrar/",
        auth_views.LoginView.as_view(
            template_name="core/login.html",
            redirect_authenticated_user=True,
        ),
        name="login",
    ),

    path(
        "sair/",
        auth_views.LogoutView.as_view(),
        name="logout",
    ),

    path(
        "minha-conta/",
        views.minha_conta,
        name="minha_conta",
    ),

    path(
        "minha-conta/seguranca/alterar-senha/",
        views.alterar_senha,
        name="alterar_senha",
    ),

    path(
        "minha-conta/assinatura/<int:assinatura_id>/renovacao-automatica/",
        views.alterar_renovacao_automatica,
        name="alterar_renovacao_automatica",
    ),

    path(
        "minha-conta/empresa/<int:empresa_id>/editar/",
        views.editar_empresa,
        name="editar_empresa",
    ),

    path(
        "minha-conta/profissional/<int:profissional_id>/editar/",
        views.editar_profissional,
        name="editar_profissional",
    ),

    path(
        "planos/<int:plano_id>/selecionar/",
        views.selecionar_plano,
        name="selecionar_plano",
    ),

    path(
        "planos/<int:plano_id>/empresa/<int:empresa_id>/alterar/",
        views.alterar_plano_empresa,
        name="alterar_plano_empresa",
    ),

    path(
        "planos/<int:plano_id>/profissional/<int:profissional_id>/alterar/",
        views.alterar_plano_profissional,
        name="alterar_plano_profissional",
    ),

    path(
        "<slug:cidade_slug>/",
        views.cidade_home,
        name="cidade_home",
    ),

    path(
        "<slug:cidade_slug>/categoria/<slug:categoria_slug>/",
        views.categoria,
        name="categoria",
    ),

    path(
        "<slug:cidade_slug>/empresa/<slug:empresa_slug>/",
        views.empresa_detalhe,
        name="empresa_detalhe",
    ),

    path(
        "<slug:cidade_slug>/profissionais/<slug:profissional_slug>/",
        views.profissional_detalhe,
        name="profissional_detalhe",
    ),

]