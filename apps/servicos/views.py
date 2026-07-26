from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.http import Http404
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_POST

from apps.empresas.models import Empresa
from apps.profissionais.models import Profissional

from .forms import ServicoForm
from .models import Servico


def _servico_do_usuario(servico, usuario):
    if servico.empresa and servico.empresa.usuario_id == usuario.id:
        return True
    if servico.profissional and servico.profissional.usuario_id == usuario.id:
        return True
    return False


@login_required
def gerenciar_empresa(request, empresa_id):
    empresa = get_object_or_404(
        Empresa,
        pk=empresa_id,
        usuario=request.user,
    )

    if request.method == "POST":
        instancia = Servico(
            empresa=empresa,
            profissional=None,
            cidade=empresa.cidade,
        )
        form = ServicoForm(
            request.POST,
            instance=instancia,
        )
        if form.is_valid():
            servico = form.save(commit=False)
            servico.empresa = empresa
            servico.profissional = None
            servico.cidade = empresa.cidade
            servico.full_clean()
            servico.save()
            messages.success(request, "Serviço cadastrado com sucesso.")
            return redirect(
                "servicos:gerenciar_empresa",
                empresa_id=empresa.pk,
            )
    else:
        form = ServicoForm()

    servicos = (
        Servico.objects
        .filter(empresa=empresa, profissional__isnull=True)
        .order_by("-ativo", "nome")
    )

    return render(
        request,
        "servicos/gerenciar.html",
        {
            "form": form,
            "servicos": servicos,
            "tipo_titular": "Empresa",
            "titular": empresa.nome_fantasia,
        },
    )


@login_required
def gerenciar_profissional(request, profissional_id):
    profissional = get_object_or_404(
        Profissional,
        pk=profissional_id,
        usuario=request.user,
    )

    if request.method == "POST":
        instancia = Servico(
            empresa=None,
            profissional=profissional,
            cidade=profissional.cidade,
        )
        form = ServicoForm(
            request.POST,
            instance=instancia,
        )
        if form.is_valid():
            servico = form.save(commit=False)
            servico.empresa = None
            servico.profissional = profissional
            servico.cidade = profissional.cidade
            servico.full_clean()
            servico.save()
            messages.success(request, "Serviço cadastrado com sucesso.")
            return redirect(
                "servicos:gerenciar_profissional",
                profissional_id=profissional.pk,
            )
    else:
        form = ServicoForm()

    servicos = (
        Servico.objects
        .filter(profissional=profissional, empresa__isnull=True)
        .order_by("-ativo", "nome")
    )

    return render(
        request,
        "servicos/gerenciar.html",
        {
            "form": form,
            "servicos": servicos,
            "tipo_titular": "Profissional",
            "titular": profissional.nome,
        },
    )


@login_required
def editar(request, servico_id):
    servico = get_object_or_404(
        Servico.objects.select_related("empresa", "profissional"),
        pk=servico_id,
    )

    if not _servico_do_usuario(servico, request.user):
        raise Http404

    if request.method == "POST":
        form = ServicoForm(request.POST, instance=servico)
        if form.is_valid():
            servico = form.save(commit=False)
            servico.full_clean()
            servico.save()
            messages.success(request, "Serviço atualizado com sucesso.")

            if servico.empresa:
                return redirect(
                    "servicos:gerenciar_empresa",
                    empresa_id=servico.empresa_id,
                )

            return redirect(
                "servicos:gerenciar_profissional",
                profissional_id=servico.profissional_id,
            )
    else:
        form = ServicoForm(instance=servico)

    return render(
        request,
        "servicos/editar.html",
        {
            "form": form,
            "servico": servico,
        },
    )


@require_POST
@login_required
def alternar_ativo(request, servico_id):
    servico = get_object_or_404(
        Servico.objects.select_related("empresa", "profissional"),
        pk=servico_id,
    )

    if not _servico_do_usuario(servico, request.user):
        raise Http404

    servico.ativo = not servico.ativo
    servico.save(update_fields=["ativo"])
    messages.success(request, "Status do serviço atualizado.")

    if servico.empresa:
        return redirect(
            "servicos:gerenciar_empresa",
            empresa_id=servico.empresa_id,
        )

    return redirect(
        "servicos:gerenciar_profissional",
        profissional_id=servico.profissional_id,
    )


@require_POST
@login_required
def excluir(request, servico_id):
    servico = get_object_or_404(
        Servico.objects.select_related("empresa", "profissional"),
        pk=servico_id,
    )

    if not _servico_do_usuario(servico, request.user):
        raise Http404

    empresa_id = servico.empresa_id
    profissional_id = servico.profissional_id
    servico.delete()
    messages.success(request, "Serviço excluído.")

    if empresa_id:
        return redirect(
            "servicos:gerenciar_empresa",
            empresa_id=empresa_id,
        )

    return redirect(
        "servicos:gerenciar_profissional",
        profissional_id=profissional_id,
    )
