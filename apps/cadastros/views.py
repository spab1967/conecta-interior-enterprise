from django.shortcuts import (
    redirect,
    render,
)

from apps.planos.models import Plano

from .forms import SolicitacaoCadastroForm


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