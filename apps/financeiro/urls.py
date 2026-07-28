from django.urls import path

from . import views

app_name = "financeiro"

urlpatterns = [

    path(
        "pagamento/<int:pedido_id>/",
        views.pagamento,
        name="pagamento",
    ),

    path(
        "confirmar/<int:pagamento_id>/",
        views.confirmar_pagamento,
        name="confirmar",
    ),
    path(
        "mercado-pago/webhook/",
        views.webhook_mercado_pago,
        name="webhook_mercado_pago",
    ),

   path(
        "historico/",
        views.historico,
        name="historico",
    ),

    path(
        "sucesso/",
        views.sucesso,
        name="sucesso",
    ),

]