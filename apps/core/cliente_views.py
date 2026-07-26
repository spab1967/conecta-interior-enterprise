from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, redirect, render

from apps.empresas.models import Empresa
from apps.profissionais.models import Profissional

from .forms import (
    EmpresaClienteForm,
    ProfissionalClienteForm,
)


@login_required
def editar_empresa(
    request,
    empresa_id,
):

    empresa = get_object_or_404(
        Empresa,
        pk=empresa_id,
        usuario=request.user,
    )

    if request.method == "POST":

        form = EmpresaClienteForm(
            request.POST,
            request.FILES,
            instance=empresa,
        )

        if form.is_valid():

            form.save()

            messages.success(
                request,
                "Dados da empresa atualizados com sucesso.",
            )

            return redirect(
                "core:minha_conta"
            )

    else:

        form = EmpresaClienteForm(
            instance=empresa
        )

    return render(
        request,
        "core/editar_empresa.html",
        {
            "form": form,
            "empresa": empresa,
        },
    )


@login_required
def editar_profissional(
    request,
    profissional_id,
):

    profissional = get_object_or_404(
        Profissional,
        pk=profissional_id,
        usuario=request.user,
    )

    if request.method == "POST":

        form = ProfissionalClienteForm(
            request.POST,
            request.FILES,
            instance=profissional,
        )

        if form.is_valid():

            form.save()

            messages.success(
                request,
                "Dados profissionais atualizados com sucesso.",
            )

            return redirect(
                "core:minha_conta"
            )

    else:

        form = ProfissionalClienteForm(
            instance=profissional
        )

    return render(
        request,
        "core/editar_profissional.html",
        {
            "form": form,
            "profissional": profissional,
        },
    )