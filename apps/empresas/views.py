from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.db.models import Q
from django.shortcuts import get_object_or_404, redirect, render

from .forms import EmpresaClienteForm
from .models import Empresa


@login_required
def listar_empresas(request):

    pesquisa = request.GET.get("q", "").strip()[:100]

    empresas = Empresa.objects.select_related(
        "cidade",
        "categoria",
    ).filter(
        usuario=request.user,
    )

    if pesquisa:

        empresas = empresas.filter(

            Q(nome_fantasia__icontains=pesquisa)
            |
            Q(descricao__icontains=pesquisa)
            |
            Q(bairro__icontains=pesquisa)

        )

    empresas = empresas.order_by(
        "-destaque",
        "nome_fantasia",
    )

    paginator = Paginator(empresas, 20)

    page = request.GET.get("page")

    page_obj = paginator.get_page(page)

    return render(
        request,
        "empresas/listar.html",
        {
            "page_obj": page_obj,
            "pesquisa": pesquisa,
        },
    )


@login_required
def visualizar_empresa(request, pk):

    empresa = get_object_or_404(
        Empresa.objects.select_related(
            "cidade",
            "categoria",
        ),
        pk=pk,
        usuario=request.user,
    )

    return render(
        request,
        "empresas/detalhe.html",
        {
            "empresa": empresa,
        },
    )


@login_required
def editar_empresa(request, pk):

    empresa = get_object_or_404(
        Empresa,
        pk=pk,
        usuario=request.user,
    )

    form = EmpresaClienteForm(
        request.POST or None,
        request.FILES or None,
        instance=empresa,
    )

    if form.is_valid():

        form.save()

        return redirect(
            "empresas:visualizar",
            pk=empresa.pk,
        )

    return render(
        request,
        "empresas/form.html",
        {
            "form": form,
            "empresa": empresa,
        },
    )
