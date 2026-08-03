from django.contrib import messages
from django.http import Http404
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_POST

from apps.empresas.models import Empresa
from apps.profissionais.models import Profissional
from apps.planos.services import filtrar_publicaveis, situacao_financeira

from .models import Favorito


def obter_identificador(request):
    """
    Usa a sessão do Django para identificar o visitante.
    """

    if not request.session.session_key:
        request.session.create()

    return request.session.session_key


def meus_favoritos(request):

    identificador = obter_identificador(request)

    favoritos_empresas = (
        Favorito.objects.filter(
            identificador=identificador,
            empresa__isnull=False,
            empresa__ativa=True,
        )
        .select_related(
            "empresa",
            "empresa__cidade",
            "empresa__categoria",
        )
        .order_by(
            "-criado_em"
        )
    )

    favoritos_profissionais = (
        Favorito.objects.filter(
            identificador=identificador,
            profissional__isnull=False,
            profissional__ativo=True,
        )
        .select_related(
            "profissional",
            "profissional__cidade",
            "profissional__categoria",
        )
        .order_by(
            "-criado_em"
        )
    )

    empresas_publicas = filtrar_publicaveis(
        Empresa.objects.filter(
            pk__in=favoritos_empresas.values_list("empresa_id", flat=True)
        ),
        "empresa",
    )
    profissionais_publicos = filtrar_publicaveis(
        Profissional.objects.filter(
            pk__in=favoritos_profissionais.values_list("profissional_id", flat=True)
        ),
        "profissional",
    )
    favoritos_empresas = favoritos_empresas.filter(empresa__in=empresas_publicas)
    favoritos_profissionais = favoritos_profissionais.filter(
        profissional__in=profissionais_publicos
    )

    return render(
        request,
        "favoritos/meus_favoritos.html",
        {
            "favoritos_empresas": favoritos_empresas,
            "favoritos_profissionais": favoritos_profissionais,
            "total_empresas": favoritos_empresas.count(),
            "total_profissionais": favoritos_profissionais.count(),
        },
    )


@require_POST
def alternar_empresa(
    request,
    cidade_slug,
    empresa_slug,
):

    empresa = get_object_or_404(
        Empresa,
        cidade__slug=cidade_slug,
        slug=empresa_slug,
        ativa=True,
    )

    if not situacao_financeira(empresa=empresa).pagina_publica:
        raise Http404

    identificador = obter_identificador(request)

    favorito = Favorito.objects.filter(
        identificador=identificador,
        empresa=empresa,
    ).first()

    if favorito:

        favorito.delete()

        messages.success(
            request,
            f"{empresa.nome_fantasia} foi removida dos seus favoritos.",
        )

    else:

        Favorito.objects.create(
            identificador=identificador,
            empresa=empresa,
        )

        messages.success(
            request,
            f"{empresa.nome_fantasia} foi adicionada aos seus favoritos.",
        )

    return redirect(
        "core:empresa_detalhe",
        cidade_slug=empresa.cidade.slug,
        empresa_slug=empresa.slug,
    )


@require_POST
def alternar_profissional(
    request,
    cidade_slug,
    profissional_slug,
):

    profissional = get_object_or_404(
        Profissional,
        cidade__slug=cidade_slug,
        slug=profissional_slug,
        ativo=True,
    )

    if not situacao_financeira(profissional=profissional).pagina_publica:
        raise Http404

    identificador = obter_identificador(request)

    favorito = Favorito.objects.filter(
        identificador=identificador,
        profissional=profissional,
    ).first()

    if favorito:

        favorito.delete()

        messages.success(
            request,
            f"{profissional.nome} foi removido dos seus favoritos.",
        )

    else:

        Favorito.objects.create(
            identificador=identificador,
            profissional=profissional,
        )

        messages.success(
            request,
            f"{profissional.nome} foi adicionado aos seus favoritos.",
        )

    return redirect(
        "core:profissional_detalhe",
        cidade_slug=profissional.cidade.slug,
        profissional_slug=profissional.slug,
    )


@require_POST
def remover_empresa(
    request,
    cidade_slug,
    empresa_slug,
):

    empresa = get_object_or_404(
        Empresa,
        cidade__slug=cidade_slug,
        slug=empresa_slug,
    )

    identificador = obter_identificador(request)

    Favorito.objects.filter(
        identificador=identificador,
        empresa=empresa,
    ).delete()

    messages.success(
        request,
        f"{empresa.nome_fantasia} foi removida dos seus favoritos.",
    )

    return redirect(
        "favoritos:meus_favoritos"
    )


@require_POST
def remover_profissional(
    request,
    cidade_slug,
    profissional_slug,
):

    profissional = get_object_or_404(
        Profissional,
        cidade__slug=cidade_slug,
        slug=profissional_slug,
    )

    identificador = obter_identificador(request)

    Favorito.objects.filter(
        identificador=identificador,
        profissional=profissional,
    ).delete()

    messages.success(
        request,
        f"{profissional.nome} foi removido dos seus favoritos.",
    )

    return redirect(
        "favoritos:meus_favoritos"
    )
