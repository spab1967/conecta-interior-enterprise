from django.urls import path

from . import views

app_name = "administracao"

urlpatterns = [

    path(
        "",
        views.dashboard,
        name="dashboard",
    ),

    path(
        "painel/",
        views.painel,
        name="painel",
    ),

    path(
        "empresas/",
        views.empresas,
        name="empresas",
    ),

    path(
        "profissionais/",
        views.profissionais,
        name="profissionais",
    ),

    path(
        "assinaturas/",
        views.assinaturas,
        name="assinaturas",
    ),

    path(
        "financeiro/",
        views.financeiro,
        name="financeiro",
    ),

    path(
        "pagamentos/",
        views.pagamentos,
        name="pagamentos",
    ),

    path(
        "avaliacoes/",
        views.avaliacoes,
        name="avaliacoes",
    ),

    path(
        "metricas/",
        views.metricas,
        name="metricas",
    ),

    path(
        "solicitacoes/",
        views.solicitacoes,
        name="solicitacoes",
    ),

    path(
        "cidades/",
        views.cidades,
        name="cidades",
    ),

    path(
        "categorias/",
        views.categorias,
        name="categorias",
    ),

    path(
        "configuracoes/",
        views.configuracoes,
        name="configuracoes",
    ),


    path(
        "solicitacoes/<int:solicitacao_id>/aprovar/",
        views.aprovar_solicitacao,
        name="aprovar_solicitacao",
    ),

    path(
        "solicitacoes/<int:solicitacao_id>/recusar/",
        views.recusar_solicitacao,
        name="recusar_solicitacao",
    ),

    path(
        "servicos/",
        views.servicos,
        name="servicos",
    ),

]