from datetime import timedelta

from django.db import transaction
from django.utils import timezone

from apps.planos.models import Assinatura
from apps.planos.vigencia import calcular_vencimento_plano

from .models import Pagamento, PedidoFinanceiro


def _assinatura_futura_equivalente(
    assinatura_origem,
    plano,
):
    if not assinatura_origem.vencimento:
        return None

    inicio_novo_periodo = (
        assinatura_origem.vencimento
        + timedelta(days=1)
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
            inicio_novo_periodo = (
                assinatura_origem.vencimento
                + timedelta(days=1)
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