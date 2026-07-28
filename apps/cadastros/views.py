from django.contrib import messages
from django.contrib.auth import get_user_model, login
from django.db import transaction
from django_ratelimit.decorators import ratelimit
from django.shortcuts import (
    redirect,
    render,
)

from apps.planos.models import Plano

from .forms import SolicitacaoCadastroForm


@ratelimit(
    key="ip",
    rate="10/h",
    method="POST",
    block=True,
)
@transaction.atomic
def anuncie(request):

    plano_inicial = None

    plano_id = request.GET.get(
        "plano"
    )

    if plano_id:

        plano_inicial = (
            Plano.objects
            .filter(
                pk=plano_id,
                ativo=True,
            )
            .first()
        )

    if request.method == "POST":

        form = SolicitacaoCadastroForm(
            request.POST
        )

        if form.is_valid():

            solicitacao = form.save(
                commit=False
            )

            solicitacao.status = "pendente"

            User = get_user_model()

            limite_primeiro_nome = User._meta.get_field(
                "first_name"
            ).max_length

            usuario = User.objects.create_user(
                username=solicitacao.email,
                email=solicitacao.email,
                password=form.cleaned_data["senha"],
                first_name=(
                    solicitacao.responsavel
                    or solicitacao.nome
                )[:limite_primeiro_nome],
                is_active=True,
            )

            solicitacao.status = (
                solicitacao.STATUS_APROVADO
            )

            solicitacao.observacao_admin = (
                "Cadastro criado automaticamente pelo cliente."
            )

            solicitacao.save()

            solicitacao.criar_cadastro(
                usuario=usuario,
            )

            login(
                request,
                usuario,
                backend=(
                    "django.contrib.auth.backends."
                    "ModelBackend"
                ),
            )

            messages.success(
                request,
                (
                    "Cadastro concluído. Agora você pode "
                    "administrar sua página e escolher seu plano."
                ),
            )

            return redirect(
                "core:minha_conta"
            )

    else:

        form = SolicitacaoCadastroForm(
            plano_inicial=plano_inicial
        )

    return render(
        request,
        "cadastros/anuncie.html",
        {
            "form": form,
            "plano_selecionado":
                plano_inicial,
        },
    )


def sucesso(request):

    solicitacao_id = request.session.get(
        "ultima_solicitacao_cadastro"
    )

    return render(
        request,
        "cadastros/sucesso.html",
        {
            "solicitacao_id":
                solicitacao_id,
        },
    )
