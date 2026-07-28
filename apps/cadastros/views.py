from django.contrib.auth import get_user_model
from django.db import transaction
from django.shortcuts import (
    redirect,
    render,
)

from apps.planos.models import Plano

from .forms import SolicitacaoCadastroForm


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

            solicitacao.save()

            User = get_user_model()

            limite_primeiro_nome = User._meta.get_field(
                "first_name"
            ).max_length

            User.objects.create_user(
                username=solicitacao.email,
                email=solicitacao.email,
                password=form.cleaned_data["senha"],
                first_name=(
                    solicitacao.responsavel
                    or solicitacao.nome
                )[:limite_primeiro_nome],
                is_active=False,
            )

            request.session[
                "ultima_solicitacao_cadastro"
            ] = solicitacao.pk

            return redirect(
                "cadastros:sucesso"
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
