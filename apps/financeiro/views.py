import json
import logging
from decimal import Decimal, InvalidOperation

from PIL import Image, UnidentifiedImageError

from mercadopago.webhook import (
    InvalidWebhookSignatureError,
    WebhookSignatureValidator,
)

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.conf import settings
from django.db.models import Q
from django.http import (
    Http404,
    HttpResponse,
)
from django.views.decorators.csrf import csrf_exempt

from django.shortcuts import (
    get_object_or_404,
    redirect,
    render,
)

from .models import (
    Pagamento,
    PedidoFinanceiro,
)
from .services import (
    MercadoPagoErro,
    aprovar_pagamento,
    criar_ou_obter_pix_mercado_pago,
    dados_pix_mercado_pago,
    consultar_pagamento_mercado_pago,
    mercado_pago_ativo,
)


logger = logging.getLogger(__name__)


def _conteudo_comprovante_valido(arquivo, nome_arquivo):
    try:
        if nome_arquivo.endswith(".pdf"):
            return arquivo.read(5) == b"%PDF-"

        imagem = Image.open(arquivo)
        formato = imagem.format
        imagem.verify()
        return formato in {"JPEG", "PNG", "WEBP"}
    except (UnidentifiedImageError, OSError, ValueError):
        return False
    finally:
        arquivo.seek(0)


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

    integracao_ativa = mercado_pago_ativo()
    pix_mercado_pago = None
    erro_mercado_pago = ""

    if integracao_ativa:

        email_pagador = (
            request.user.email
            or request.user.username
        )

        if "@" not in email_pagador:
            erro_mercado_pago = (
                "Sua conta precisa possuir um e-mail válido "
                "para gerar o pagamento PIX."
            )

        else:

            try:

                resposta = (
                    criar_ou_obter_pix_mercado_pago(
                        pagamento_obj,
                        email_pagador,
                    )
                )

                if resposta.get("status") == "approved":

                    aprovar_pagamento(
                        pagamento_obj
                    )

                    messages.success(
                        request,
                        (
                            "Pagamento confirmado. "
                            "Seu plano já está ativo."
                        ),
                    )

                    return redirect(
                        "core:minha_conta"
                    )

                pix_mercado_pago = (
                    dados_pix_mercado_pago(
                        resposta
                    )
                )

                if (
                    not pix_mercado_pago["qr_code"]
                    and not pix_mercado_pago["ticket_url"]
                ):
                    erro_mercado_pago = (
                        "O PIX foi criado, mas o QR Code "
                        "ainda não está disponível. "
                        "Atualize a página em instantes."
                    )

            except MercadoPagoErro as erro:

                erro_mercado_pago = str(
                    erro
                )

            except Exception:

                logger.exception(
                    "Falha inesperada ao gerar PIX "
                    "no Mercado Pago."
                )

                erro_mercado_pago = (
                    "O Mercado Pago está temporariamente "
                    "indisponível. Tente novamente em instantes."
                )

    dados_pix_manual = {
        "favorecido": getattr(
            settings,
            "CONECTA_PIX_FAVORECIDO",
            "",
        ),
        "chave": getattr(
            settings,
            "CONECTA_PIX_CHAVE",
            "",
        ),
        "banco": getattr(
            settings,
            "CONECTA_PIX_BANCO",
            "",
        ),
    }

    return render(
        request,
        "financeiro/pagamento.html",
        {
            "pedido": pedido,
            "pagamento": pagamento_obj,
            "dados_pix": dados_pix_manual,
            "mercado_pago_ativo":
                integracao_ativa,
            "pix_mercado_pago":
                pix_mercado_pago,
            "erro_mercado_pago":
                erro_mercado_pago,
        },
    )

@csrf_exempt
def webhook_mercado_pago(request):

    if request.method != "POST":
        return HttpResponse(
            status=405
        )

    segredo = getattr(
        settings,
        "MERCADO_PAGO_WEBHOOK_SECRET",
        "",
    )

    if not segredo:
        return HttpResponse(
            status=503
        )

    try:
        corpo = json.loads(
            request.body or b"{}"
        )
    except json.JSONDecodeError:
        return HttpResponse(
            status=400
        )

    tipo = (
        request.GET.get("type")
        or corpo.get("type")
    )

    dados = corpo.get("data") or {}

    codigo = (
        request.GET.get("data.id")
        or dados.get("id")
    )

    if (
        tipo != "payment"
        or not codigo
    ):
        return HttpResponse(
            status=200
        )

    try:

        WebhookSignatureValidator.validate(
            request.headers.get(
                "x-signature"
            ),
            request.headers.get(
                "x-request-id"
            ),
            request.GET.get(
                "data.id"
            ),
            segredo,
        )

    except (
        InvalidWebhookSignatureError,
        TypeError,
        ValueError,
    ):

        return HttpResponse(
            status=401
        )

    try:

        resposta = (
            consultar_pagamento_mercado_pago(
                codigo
            )
        )

    except Exception:

        logger.exception(
            "Falha ao consultar pagamento "
            "notificado pelo Mercado Pago."
        )

        return HttpResponse(
            status=503
        )

    pagamento_obj = (
        Pagamento.objects
        .select_related(
            "pedido",
        )
        .filter(
            codigo_transacao=str(
                codigo
            ),
            status=Pagamento.STATUS_PENDENTE,
        )
        .first()
    )

    if not pagamento_obj:
        return HttpResponse(
            status=200
        )

    pedido = pagamento_obj.pedido

    try:
        valor_recebido = Decimal(
            str(
                resposta.get(
                    "transaction_amount"
                )
            )
        ).quantize(
            Decimal("0.01")
        )
    except (
        InvalidOperation,
        TypeError,
    ):
        return HttpResponse(
            status=400
        )

    referencia_valida = (
        str(
            resposta.get(
                "external_reference"
            )
        )
        == str(pedido.pk)
    )

    valor_valido = (
        valor_recebido
        == pedido.valor.quantize(
            Decimal("0.01")
        )
    )

    meio_valido = (
        resposta.get(
            "payment_method_id"
        )
        == "pix"
    )

    if not (
        referencia_valida
        and valor_valido
        and meio_valido
    ):
        logger.warning(
            "Webhook Mercado Pago rejeitado "
            "por divergência no pedido %s.",
            pedido.pk,
        )

        return HttpResponse(
            status=400
        )

    if resposta.get("status") == "approved":

        aprovar_pagamento(
            pagamento_obj
        )

    return HttpResponse(
        status=200
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
        status=Pagamento.STATUS_PENDENTE,
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

    comprovante = request.FILES.get(
        "comprovante"
    )

    if not comprovante:
        messages.error(
            request,
            "Selecione o comprovante do pagamento.",
        )

        return redirect(
            "financeiro:pagamento",
            pedido_id=pedido.pk,
        )

    extensoes_permitidas = (
        ".pdf",
        ".png",
        ".jpg",
        ".jpeg",
        ".webp",
    )

    nome_arquivo = comprovante.name.lower()

    if not nome_arquivo.endswith(
        extensoes_permitidas
    ):
        messages.error(
            request,
            "Formato inválido. Envie PDF, PNG, JPG, JPEG ou WEBP.",
        )

        return redirect(
            "financeiro:pagamento",
            pedido_id=pedido.pk,
        )

    limite = 5 * 1024 * 1024

    if comprovante.size > limite:
        messages.error(
            request,
            "O comprovante deve ter no máximo 5 MB.",
        )

        return redirect(
            "financeiro:pagamento",
            pedido_id=pedido.pk,
        )

    if not _conteudo_comprovante_valido(
        comprovante,
        nome_arquivo,
    ):
        messages.error(
            request,
            (
                "O conteúdo do comprovante não corresponde "
                "a um PDF ou imagem válida."
            ),
        )

        return redirect(
            "financeiro:pagamento",
            pedido_id=pedido.pk,
        )

    pagamento_obj.comprovante = comprovante

    pagamento_obj.save(
        update_fields=[
            "comprovante",
            "atualizado_em",
        ]
    )

    request.session[
        "ultimo_pagamento_confirmado"
    ] = pagamento_obj.pk

    messages.success(
        request,
        (
            "Comprovante enviado com sucesso. "
            "O pagamento ficará pendente até "
            "a conferência pelo administrador."
        ),
    )

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