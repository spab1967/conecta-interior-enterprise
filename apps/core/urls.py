from django.contrib.auth import views as auth_views
from django.urls import path
from django_ratelimit.decorators import ratelimit

from . import views


app_name = "core"


# Limite por identificador protege cada conta contra força bruta sem
# depender do endereço do proxy reverso do Render.
login_cliente = ratelimit(
    key="post:username",
    rate="5/5m",
    method="POST",
    block=True,
)(
    auth_views.LoginView.as_view(
        template_name="core/login.html",
        redirect_authenticated_user=True,
    )
)


urlpatterns = [

    path(
        "health/",
        views.health,
        name="health",
    ),

    path(
        "service-worker.js",
        views.service_worker,
        name="service_worker",
    ),

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
        login_cliente,
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

    # ========================================================
    # EMPRESA
    # ========================================================

    path(
        "minha-conta/empresa/<int:empresa_id>/editar/",
        views.editar_empresa,
        name="editar_empresa",
    ),

    path(
        "minha-conta/empresa/<int:empresa_id>/galeria/<int:foto_id>/excluir/",
        views.excluir_foto_empresa,
        name="excluir_foto_empresa",
    ),

    # ========================================================
    # PROFISSIONAL
    # ========================================================

    path(
        "minha-conta/profissional/<int:profissional_id>/editar/",
        views.editar_profissional,
        name="editar_profissional",
    ),

    path(
        "minha-conta/profissional/<int:profissional_id>/galeria/<int:foto_id>/excluir/",
        views.excluir_foto_profissional,
        name="excluir_foto_profissional",
    ),

    # ========================================================
    # PLANOS
    # ========================================================

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

    # ========================================================
    # PAGINAS PUBLICAS
    # ========================================================

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
