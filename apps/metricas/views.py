from datetime import timedelta

from django.contrib.auth.decorators import login_required
from django.db.models import Count
from django.db.models.functions import TruncDate
from django.http import (
    Http404,
    HttpResponseRedirect,
)
from django.shortcuts import get_object_or_404, render
from django.utils import timezone

from apps.empresas.models import Empresa
from apps.planos.services import possui_acesso_metricas
from apps.profissionais.models import Profissional

from .models import EventoContato


TIPOS_VALIDOS = {
    EventoContato.TIPO_WHATSAPP,
    EventoContato.TIPO_TELEFONE,
    EventoContato.TIPO_SITE,
    EventoContato.TIPO_INSTAGRAM,
    EventoContato.TIPO_EMAIL,
}


class HttpResponseContatoRedirect(HttpResponseRedirect):
    allowed_schemes = [
        "http",
        "https",
        "ftp",
        "tel",
        "mailto",
    ]


def _registrar_evento(
    empresa=None,
    profissional=None,
    tipo=None,
):
    EventoContato.objects.create(
        empresa=empresa,
        profissional=profissional,
        tipo=tipo,
    )


def _redirecionar_contato(destino):

    if not destino:
        raise Http404(
            "Contato não disponível."
        )

    return HttpResponseContatoRedirect(
        destino
    )


def contato_empresa(
    request,
    empresa_id,
    tipo,
):

    if tipo not in TIPOS_VALIDOS:
        raise Http404(
            "Tipo de contato inválido."
        )

    empresa = get_object_or_404(
        Empresa,
        pk=empresa_id,
        ativa=True,
    )

    destino = ""

    if tipo == EventoContato.TIPO_WHATSAPP:

        destino = empresa.whatsapp_link

    elif tipo == EventoContato.TIPO_TELEFONE:

        if empresa.telefone:

            telefone = "".join(
                filter(
                    lambda caractere:
                    caractere.isdigit()
                    or caractere == "+",
                    empresa.telefone,
                )
            )

            destino = f"tel:{telefone}"

    elif tipo == EventoContato.TIPO_SITE:

        destino = empresa.site

    elif tipo == EventoContato.TIPO_INSTAGRAM:

        destino = empresa.instagram

    elif tipo == EventoContato.TIPO_EMAIL:

        if empresa.email:
            destino = (
                f"mailto:{empresa.email}"
            )

    if not destino:
        raise Http404(
            "Contato não disponível."
        )

    _registrar_evento(
        empresa=empresa,
        tipo=tipo,
    )

    return _redirecionar_contato(
        destino
    )


def contato_profissional(
    request,
    profissional_id,
    tipo,
):

    if tipo not in TIPOS_VALIDOS:
        raise Http404(
            "Tipo de contato inválido."
        )

    profissional = get_object_or_404(
        Profissional,
        pk=profissional_id,
        ativo=True,
    )

    destino = ""

    if tipo == EventoContato.TIPO_WHATSAPP:

        destino = profissional.whatsapp_link

    elif tipo == EventoContato.TIPO_TELEFONE:

        if profissional.telefone:

            telefone = "".join(
                filter(
                    lambda caractere:
                    caractere.isdigit()
                    or caractere == "+",
                    profissional.telefone,
                )
            )

            destino = f"tel:{telefone}"

    elif tipo == EventoContato.TIPO_SITE:

        destino = profissional.site

    elif tipo == EventoContato.TIPO_INSTAGRAM:

        destino = profissional.instagram

    elif tipo == EventoContato.TIPO_EMAIL:

        if profissional.email:
            destino = (
                f"mailto:{profissional.email}"
            )

    if not destino:
        raise Http404(
            "Contato não disponível."
        )

    _registrar_evento(
        profissional=profissional,
        tipo=tipo,
    )

    return _redirecionar_contato(
        destino
    )


def _dados_painel(queryset):

    agora = timezone.now()
    hoje = timezone.localdate()

    inicio_hoje = timezone.make_aware(
        timezone.datetime.combine(
            hoje,
            timezone.datetime.min.time(),
        )
    )

    inicio_7_dias = agora - timedelta(
        days=7
    )

    inicio_30_dias = agora - timedelta(
        days=30
    )

    total = queryset.count()

    total_hoje = queryset.filter(
        criado_em__gte=inicio_hoje
    ).count()

    total_7_dias = queryset.filter(
        criado_em__gte=inicio_7_dias
    ).count()

    total_30_dias = queryset.filter(
        criado_em__gte=inicio_30_dias
    ).count()

    whatsapp = queryset.filter(
        tipo=EventoContato.TIPO_WHATSAPP
    ).count()

    telefone = queryset.filter(
        tipo=EventoContato.TIPO_TELEFONE
    ).count()

    email = queryset.filter(
        tipo=EventoContato.TIPO_EMAIL
    ).count()

    site = queryset.filter(
        tipo=EventoContato.TIPO_SITE
    ).count()

    instagram = queryset.filter(
        tipo=EventoContato.TIPO_INSTAGRAM
    ).count()

    canais = (
        queryset
        .values("tipo")
        .annotate(
            total=Count("id")
        )
        .order_by("-total")
    )

    ultimos_eventos = (
        queryset
        .order_by("-criado_em")[:20]
    )

    contatos_por_dia_query = (
        queryset
        .filter(
            criado_em__gte=inicio_30_dias
        )
        .annotate(
            dia=TruncDate("criado_em")
        )
        .values("dia")
        .annotate(
            total=Count("id")
        )
        .order_by("dia")
    )

    contatos_por_dia_dict = {
        item["dia"]: item["total"]
        for item in contatos_por_dia_query
    }

    evolucao_30_dias = []

    for deslocamento in range(29, -1, -1):

        dia = hoje - timedelta(
            days=deslocamento
        )

        evolucao_30_dias.append(
            {
                "dia": dia,
                "total": contatos_por_dia_dict.get(
                    dia,
                    0,
                ),
            }
        )

    maior_dia = max(
        (
            item["total"]
            for item in evolucao_30_dias
        ),
        default=0,
    )

    if maior_dia == 0:
        maior_dia = 1

    for item in evolucao_30_dias:

        item["percentual"] = round(
            (
                item["total"]
                / maior_dia
            )
            * 100
        )

    return {
        "total": total,
        "hoje": total_hoje,
        "sete_dias": total_7_dias,
        "trinta_dias": total_30_dias,
        "whatsapp": whatsapp,
        "telefone": telefone,
        "email": email,
        "site": site,
        "instagram": instagram,
        "canais": canais,
        "ultimos_eventos": ultimos_eventos,
        "evolucao_30_dias": evolucao_30_dias,
    }


def _usuario_pode_acessar_empresa(
    usuario,
    empresa,
):

    if usuario.is_staff or usuario.is_superuser:
        return True

    return (
        empresa.usuario_id
        == usuario.id
    )


def _usuario_pode_acessar_profissional(
    usuario,
    profissional,
):

    if usuario.is_staff or usuario.is_superuser:
        return True

    return (
        profissional.usuario_id
        == usuario.id
    )


@login_required
def painel_empresa(
    request,
    empresa_id,
):

    empresa = get_object_or_404(
        Empresa.objects.select_related(
            "cidade",
            "categoria",
            "usuario",
        ),
        pk=empresa_id,
    )

    if not _usuario_pode_acessar_empresa(
        request.user,
        empresa,
    ):
        raise Http404(
            "Painel não encontrado."
        )

    if not possui_acesso_metricas(
        empresa=empresa
    ):
        raise Http404(
            "O plano atual desta empresa não possui "
            "acesso ao painel de métricas."
        )

    eventos = EventoContato.objects.filter(
        empresa=empresa
    )

    dados = _dados_painel(
        eventos
    )

    return render(
        request,
        "metricas/painel_individual.html",
        {
            "tipo_perfil": "Empresa",
            "nome_perfil": empresa.nome_fantasia,
            "cidade_perfil": empresa.cidade.nome,
            "objeto": empresa,
            "painel_cliente": not request.user.is_staff,
            **dados,
        },
    )


@login_required
def painel_profissional(
    request,
    profissional_id,
):

    profissional = get_object_or_404(
        Profissional.objects.select_related(
            "cidade",
            "categoria",
            "empresa",
            "usuario",
        ),
        pk=profissional_id,
    )

    if not _usuario_pode_acessar_profissional(
        request.user,
        profissional,
    ):
        raise Http404(
            "Painel não encontrado."
        )

    if not possui_acesso_metricas(
        profissional=profissional
    ):
        raise Http404(
            "O plano atual deste profissional não possui "
            "acesso ao painel de métricas."
        )

    eventos = EventoContato.objects.filter(
        profissional=profissional
    )

    dados = _dados_painel(
        eventos
    )

    return render(
        request,
        "metricas/painel_individual.html",
        {
            "tipo_perfil": "Profissional",
            "nome_perfil": profissional.nome,
            "cidade_perfil": profissional.cidade.nome,
            "objeto": profissional,
            "painel_cliente": not request.user.is_staff,
            **dados,
        },
    )