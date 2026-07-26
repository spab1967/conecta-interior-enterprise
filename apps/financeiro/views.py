from django.contrib.auth.decorators import login_required
from django.db.models import Q
from django.http import Http404
from django.shortcuts import (
    get_object_or_404,
    redirect,
    render,
)

from .models import (
    Pagamento,
    PedidoFinanceiro,
)
from .services import aprovar_pagamento


def _pedido_pertence_ao_usuario(
    pedido,
    usuario,
):

    if (
        pedido.empresa
        and pedido.empresa.usuario_id
        == usuario.id
    ):
        return True

    if (
        pedido.profissional
        and pedido.profissional.usuario_id
        == usuario.id
    ):
        return True

    return False


@login_required
def pagamento(
    request,
    pedido_id,
):

    pedido = get_object_or_404(
        PedidoFinanceiro.objects.select_related(
            "empresa",
            "profissional",
            "plano",
        ),
        pk=pedido_id,
        status=PedidoFinanceiro.STATUS_PENDENTE,
    )

    if not _pedido_pertence_ao_usuario(
        pedido,
        request.user,
    ):
        raise Http404

    pagamento_obj, criado = (
        Pagamento.objects.get_or_create(
            pedido=pedido,
            status=Pagamento.STATUS_PENDENTE,
            defaults={
                "valor": pedido.valor,
                "tipo": Pagamento.TIPO_PIX,
            },
        )
    )

    return render(
        request,
        "financeiro/pagamento.html",
        {
            "pedido": pedido,
            "pagamento": pagamento_obj,
        },
    )


@login_required
def confirmar_pagamento(
    request,
    pagamento_id,
):

    if request.method != "POST":
        return redirect(
            "core:minha_conta"
        )

    pagamento_obj = get_object_or_404(
        Pagamento.objects.select_related(
            "pedido__empresa",
            "pedido__profissional",
            "pedido__plano",
        ),
        pk=pagamento_id,
    )

    pedido = pagamento_obj.pedido

    if not _pedido_pertence_ao_usuario(
        pedido,
        request.user,
    ):
        raise Http404

    if (
        pedido.status
        != PedidoFinanceiro.STATUS_PENDENTE
    ):
        return redirect(
            "core:minha_conta"
        )

    aprovar_pagamento(
        pagamento_obj
    )

    request.session[
        "ultimo_pagamento_confirmado"
    ] = pagamento_obj.pk

    return redirect(
        "financeiro:sucesso"
    )


@login_required
def sucesso(request):

    pagamento_id = request.session.get(
        "ultimo_pagamento_confirmado"
    )

    pagamento_obj = None

    if pagamento_id:

        pagamento_obj = (
            Pagamento.objects
            .select_related(
                "pedido__plano",
                "pedido__empresa",
                "pedido__profissional",
            )
            .filter(
                pk=pagamento_id
            )
            .first()
        )

        if (
            pagamento_obj
            and not _pedido_pertence_ao_usuario(
                pagamento_obj.pedido,
                request.user,
            )
        ):
            pagamento_obj = None

    return render(
        request,
        "financeiro/sucesso.html",
        {
            "pagamento":
                pagamento_obj,
        },
    )
@login_required
def historico(request):

    pedidos = (
        PedidoFinanceiro.objects
        .select_related(
            "empresa",
            "profissional",
            "plano",
            "assinatura",
        )
        .prefetch_related(
            "pagamentos",
        )
        .filter(
            Q(
                empresa__usuario=request.user
            )
            | Q(
                profissional__usuario=request.user
            )
        )
        .distinct()
        .order_by(
            "-criado_em"
        )
    )

    return render(
        request,
        "financeiro/historico.html",
        {
            "pedidos": pedidos,
        },
    )