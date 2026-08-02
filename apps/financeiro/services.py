from datetime import timedelta
from decimal import Decimal
from uuid import NAMESPACE_URL, uuid5

import mercadopago
from mercadopago.config import RequestOptions

from django.conf import settings
from django.db import transaction
from django.utils import timezone

from apps.planos.models import Assinatura
from apps.planos.vigencia import calcular_vencimento_plano

from .models import Pagamento, PedidoFinanceiro


class MercadoPagoErro(Exception):
    """Falha segura na comunicação com o processador."""


def mercado_pago_ativo():
    return bool(
        getattr(
            settings,
            "MERCADO_PAGO_ACCESS_TOKEN",
            "",
        )
        and getattr(
            settings,
            "MERCADO_PAGO_WEBHOOK_SECRET",
            "",
        )
    )


def _mercado_pago_sdk():
    token = getattr(
        settings,
        "MERCADO_PAGO_ACCESS_TOKEN",
        "",
    )

    if not token:
        raise MercadoPagoErro(
            "A integração do Mercado Pago ainda não foi configurada."
        )

    return mercadopago.SDK(token)


def _normalizar_retorno_mercado_pago(
    resultado,
):
    codigo_http = resultado.get(
        "status"
    )

    resposta = (
        resultado.get("response")
        or {}
    )

    if codigo_http not in (
        200,
        201,
    ):
        mensagem = (
            resposta.get("message")
            or resposta.get("error")
            or (
                "Não foi possível gerar "
                "o pagamento PIX."
            )
        )

        raise MercadoPagoErro(
            str(mensagem)
        )

    return resposta


def consultar_pagamento_mercado_pago(
    codigo_transacao,
):
    resultado = (
        _mercado_pago_sdk()
        .payment()
        .get(
            str(codigo_transacao)
        )
    )

    return (
        _normalizar_retorno_mercado_pago(
            resultado
        )
    )


def criar_ou_obter_pix_mercado_pago(
    pagamento,
    email_pagador,
):
    if pagamento.codigo_transacao:
        return (
            consultar_pagamento_mercado_pago(
                pagamento.codigo_transacao
            )
        )

    pedido = pagamento.pedido

    chave = str(
        uuid5(
            NAMESPACE_URL,
            (
                "conecta-interior:"
                f"pagamento:{pagamento.pk}"
            ),
        )
    )

    opcoes = RequestOptions()

    opcoes.custom_headers = {
        "x-idempotency-key": chave,
    }

    dados = {
        "transaction_amount": float(
            Decimal(pedido.valor)
        ),
        "description": (
            f"ConectaInterior — Plano "
            f"{pedido.plano.nome}"
        )[:255],
        "payment_method_id": "pix",
        "external_reference": str(
            pedido.pk
        ),
        "payer": {
            "email": email_pagador,
        },
        "metadata": {
            "pedido_financeiro_id":
                pedido.pk,
            "pagamento_local_id":
                pagamento.pk,
        },
    }

    resultado = (
        _mercado_pago_sdk()
        .payment()
        .create(
            dados,
            opcoes,
        )
    )

    resposta = (
        _normalizar_retorno_mercado_pago(
            resultado
        )
    )

    codigo = resposta.get("id")

    if not codigo:
        raise MercadoPagoErro(
            "O Mercado Pago não retornou "
            "o identificador da cobrança."
        )

    pagamento.codigo_transacao = str(
        codigo
    )

    pagamento.save(
        update_fields=[
            "codigo_transacao",
            "atualizado_em",
        ]
    )

    return resposta


def dados_pix_mercado_pago(
    resposta,
):
    transacao = (
        resposta
        .get(
            "point_of_interaction",
            {},
        )
        .get(
            "transaction_data",
            {},
        )
    )

    return {
        "codigo_transacao":
            str(
                resposta.get("id")
                or ""
            ),
        "status":
            resposta.get(
                "status",
                "",
            ),
        "status_detalhado":
            resposta.get(
                "status_detail",
                "",
            ),
        "qr_code":
            transacao.get(
                "qr_code",
                "",
            ),
        "qr_code_base64":
            transacao.get(
                "qr_code_base64",
                "",
            ),
        "ticket_url":
            transacao.get(
                "ticket_url",
                "",
            ),
    }


def _assinatura_futura_equivalente(
    assinatura_origem,
    plano,
):
    if not assinatura_origem.vencimento:
        return None

    inicio_novo_periodo = max(
        assinatura_origem.vencimento + timedelta(days=1),
        timezone.localdate(),
    )

    novo_vencimento = calcular_vencimento_plano(
        plano,
        inicio_novo_periodo,
    )

    filtros = {
        "plano": plano,
        "status": Assinatura.STATUS_ATIVA,
        "inicio": inicio_novo_periodo,
        "vencimento": novo_vencimento,
    }

    if assinatura_origem.empresa_id:
        filtros["empresa_id"] = assinatura_origem.empresa_id
        filtros["profissional__isnull"] = True
    else:
        filtros["profissional_id"] = assinatura_origem.profissional_id
        filtros["empresa__isnull"] = True

    return (
        Assinatura.objects
        .filter(**filtros)
        .exclude(pk=assinatura_origem.pk)
        .order_by("id")
        .first()
    )


@transaction.atomic
def aprovar_pagamento(pagamento):

    if pagamento.status == Pagamento.STATUS_APROVADO:
        return pagamento

    pedido = pagamento.pedido
    hoje = timezone.localdate()

    pagamento.status = Pagamento.STATUS_APROVADO
    pagamento.pago_em = timezone.now()
    pagamento.save(
        update_fields=[
            "status",
            "pago_em",
        ]
    )

    pedido.status = PedidoFinanceiro.STATUS_PAGO
    pedido.save(
        update_fields=[
            "status",
        ]
    )

    titular = pedido.empresa or pedido.profissional
    if titular and titular.liberacao_financeira_ativa:
        titular.liberacao_financeira_ativa = False
        titular.save(update_fields=["liberacao_financeira_ativa"])

    assinatura_origem = pedido.assinatura

    # RENOVAÇÃO
    #
    # Se o pedido já estava vinculado a uma assinatura,
    # significa que foi gerado pelo processo de renovação.
    if assinatura_origem:

        existente = _assinatura_futura_equivalente(
            assinatura_origem,
            pedido.plano,
        )

        if existente:

            if (
                existente.renovacao_automatica
                != assinatura_origem.renovacao_automatica
            ):
                existente.renovacao_automatica = (
                    assinatura_origem.renovacao_automatica
                )
                existente.save(
                    update_fields=[
                        "renovacao_automatica",
                    ]
                )

            pedido.assinatura = existente
            pedido.save(
                update_fields=[
                    "assinatura",
                ]
            )

            return pagamento

        inicio_novo_periodo = hoje

        if assinatura_origem.vencimento:
            inicio_novo_periodo = max(
                assinatura_origem.vencimento + timedelta(days=1),
                hoje,
            )

        novo_vencimento = calcular_vencimento_plano(
            pedido.plano,
            inicio_novo_periodo,
        )

        nova = Assinatura.objects.create(
            empresa=pedido.empresa,
            profissional=pedido.profissional,
            plano=pedido.plano,
            status=Assinatura.STATUS_ATIVA,
            inicio=inicio_novo_periodo,
            vencimento=novo_vencimento,
            renovacao_automatica=(
                assinatura_origem.renovacao_automatica
            ),
            observacoes=(
                "Assinatura criada por renovação "
                "no módulo financeiro."
            ),
        )

        pedido.assinatura = nova

        pedido.save(
            update_fields=[
                "assinatura",
            ]
        )

        return pagamento

    # NOVA CONTRATAÇÃO OU TROCA DE PLANO

    if pedido.empresa:

        Assinatura.objects.filter(
            empresa=pedido.empresa,
            profissional__isnull=True,
            status=Assinatura.STATUS_ATIVA,
        ).update(
            status=Assinatura.STATUS_CANCELADA,
        )

    else:

        Assinatura.objects.filter(
            profissional=pedido.profissional,
            empresa__isnull=True,
            status=Assinatura.STATUS_ATIVA,
        ).update(
            status=Assinatura.STATUS_CANCELADA,
        )

    nova = Assinatura.objects.create(
        empresa=pedido.empresa,
        profissional=pedido.profissional,
        plano=pedido.plano,
        status=Assinatura.STATUS_ATIVA,
        inicio=hoje,
        vencimento=calcular_vencimento_plano(
            pedido.plano,
            hoje,
        ),
        renovacao_automatica=False,
        observacoes=(
            "Assinatura criada pelo módulo financeiro."
        ),
    )

    pedido.assinatura = nova

    pedido.save(
        update_fields=[
            "assinatura",
        ]
    )

    return pagamento


@transaction.atomic
def gerar_pedido_renovacao(
    assinatura,
):

    if assinatura.status != Assinatura.STATUS_ATIVA:
        return None

    if not assinatura.renovacao_automatica:
        return None

    if not assinatura.vencimento:
        return None

    assinatura_futura = _assinatura_futura_equivalente(
        assinatura,
        assinatura.plano,
    )

    if assinatura_futura:
        return None

    pedido_existente = (
        PedidoFinanceiro.objects
        .filter(
            assinatura=assinatura,
            status=PedidoFinanceiro.STATUS_PENDENTE,
        )
        .first()
    )

    if pedido_existente:
        return pedido_existente

    pedido = PedidoFinanceiro.objects.create(
        empresa=assinatura.empresa,
        profissional=assinatura.profissional,
        plano=assinatura.plano,
        assinatura=assinatura,
        valor=assinatura.plano.preco_mensal,
        status=PedidoFinanceiro.STATUS_PENDENTE,
        observacoes=(
            "Pedido de renovação da assinatura."
        ),
    )

    Pagamento.objects.create(
        pedido=pedido,
        tipo=Pagamento.TIPO_PIX,
        status=Pagamento.STATUS_PENDENTE,
        valor=pedido.valor,
    )

    return pedido
