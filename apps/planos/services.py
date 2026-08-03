from dataclasses import dataclass
from datetime import timedelta

from django.utils import timezone

from .models import Assinatura


DIAS_TOLERANCIA = 7
STATUS_REGULAR = "regular"
STATUS_ATRASO = "atraso"
STATUS_SUSPENSA = "suspensa"
STATUS_LIBERADA = "liberada"
PLANOS_COM_PAGINA_PUBLICA = {"destaque", "premium"}


@dataclass(frozen=True)
class SituacaoFinanceira:
    codigo: str
    rotulo: str
    assinatura: object = None
    vencimento: object = None
    limite_tolerancia: object = None
    plano_publicavel: bool = False

    @property
    def pagina_publica(self):
        return self.plano_publicavel and self.codigo != STATUS_SUSPENSA


def _plano_permite_pagina(assinatura):
    return bool(
        assinatura
        and assinatura.plano.ativo
        and assinatura.plano.nome.strip().casefold() in PLANOS_COM_PAGINA_PUBLICA
    )


def _liberacao_manual_valida(titular, hoje):
    return bool(
        titular.liberacao_financeira_ativa
        and (
            titular.liberacao_financeira_ate is None
            or titular.liberacao_financeira_ate >= hoje
        )
    )


def assinatura_financeira(empresa=None, profissional=None):
    titular = empresa if empresa is not None else profissional
    cache = getattr(titular, "_prefetched_objects_cache", {}) if titular else {}
    if "assinaturas" in cache:
        candidatas = [
            assinatura for assinatura in cache["assinaturas"]
            if assinatura.status in (
                Assinatura.STATUS_ATIVA, Assinatura.STATUS_VENCIDA,
            )
        ]
        return max(
            candidatas,
            key=lambda assinatura: (assinatura.inicio, assinatura.criada_em),
            default=None,
        )

    queryset = Assinatura.objects.select_related("plano").filter(
        status__in=(Assinatura.STATUS_ATIVA, Assinatura.STATUS_VENCIDA),
    )
    if empresa is not None:
        queryset = queryset.filter(empresa=empresa, profissional__isnull=True)
    elif profissional is not None:
        queryset = queryset.filter(profissional=profissional, empresa__isnull=True)
    else:
        return None
    return queryset.order_by("-inicio", "-criada_em").first()


def situacao_financeira(empresa=None, profissional=None, hoje=None):
    hoje = hoje or timezone.localdate()
    titular = empresa if empresa is not None else profissional
    if titular is None:
        raise ValueError("Informe uma empresa ou um profissional.")

    assinatura = assinatura_financeira(empresa=empresa, profissional=profissional)
    plano_publicavel = _plano_permite_pagina(assinatura)

    if plano_publicavel and _liberacao_manual_valida(titular, hoje):
        return SituacaoFinanceira(
            STATUS_LIBERADA, "Liberada manualmente", assinatura,
            getattr(assinatura, "vencimento", None),
            plano_publicavel=True,
        )

    if not plano_publicavel:
        return SituacaoFinanceira(
            STATUS_REGULAR, "Regular", assinatura, plano_publicavel=False,
        )

    vencimento = assinatura.vencimento
    if not vencimento or vencimento >= hoje:
        return SituacaoFinanceira(
            STATUS_REGULAR, "Regular", assinatura, vencimento,
            plano_publicavel=True,
        )

    limite = vencimento + timedelta(days=DIAS_TOLERANCIA)
    if hoje <= limite:
        return SituacaoFinanceira(
            STATUS_ATRASO, "Em atraso — período de tolerância",
            assinatura, vencimento, limite, plano_publicavel=True,
        )

    return SituacaoFinanceira(
        STATUS_SUSPENSA, "Suspensa por inadimplência",
        assinatura, vencimento, limite, plano_publicavel=True,
    )


def filtrar_publicaveis(queryset, tipo):
    objetos = list(queryset.prefetch_related("assinaturas__plano"))
    ids = []
    for objeto in objetos:
        kwargs = {tipo: objeto}
        if situacao_financeira(**kwargs).pagina_publica:
            ids.append(objeto.pk)
    return queryset.filter(pk__in=ids)


def assinatura_vigente(
    empresa=None,
    profissional=None,
):

    hoje = timezone.localdate()

    queryset = (
        Assinatura.objects
        .select_related("plano")
        .filter(
            status=Assinatura.STATUS_ATIVA,
            inicio__lte=hoje,
            plano__ativo=True,
        )
    )

    if empresa is not None:

        queryset = queryset.filter(
            empresa=empresa,
            profissional__isnull=True,
        )

    elif profissional is not None:

        queryset = queryset.filter(
            profissional=profissional,
            empresa__isnull=True,
        )

    else:
        return None

    limite = hoje - timedelta(days=DIAS_TOLERANCIA)
    queryset = queryset.filter(
        vencimento__isnull=True
    ) | queryset.filter(
        vencimento__gte=limite
    )

    return (
        queryset
        .order_by(
            "-inicio",
            "-criada_em",
        )
        .first()
    )


def plano_vigente(
    empresa=None,
    profissional=None,
):

    assinatura = assinatura_vigente(
        empresa=empresa,
        profissional=profissional,
    )

    if assinatura:
        return assinatura.plano

    return None


def possui_acesso_metricas(
    empresa=None,
    profissional=None,
):

    plano = plano_vigente(
        empresa=empresa,
        profissional=profissional,
    )

    return bool(
        plano
        and plano.acesso_metricas
    )


def possui_destaque_busca(
    empresa=None,
    profissional=None,
):

    plano = plano_vigente(
        empresa=empresa,
        profissional=profissional,
    )

    return bool(
        plano
        and plano.destaque_busca
    )


def possui_destaque_perfil(
    empresa=None,
    profissional=None,
):

    plano = plano_vigente(
        empresa=empresa,
        profissional=profissional,
    )

    return bool(
        plano
        and plano.destaque_perfil
    )


def possui_prioridade_resultados(
    empresa=None,
    profissional=None,
):

    plano = plano_vigente(
        empresa=empresa,
        profissional=profissional,
    )

    return bool(
        plano
        and plano.prioridade_resultados
    )


def possui_selo_destaque(
    empresa=None,
    profissional=None,
):

    plano = plano_vigente(
        empresa=empresa,
        profissional=profissional,
    )

    return bool(
        plano
        and plano.selo_destaque
    )


def limite_fotos(
    empresa=None,
    profissional=None,
):

    plano = plano_vigente(
        empresa=empresa,
        profissional=profissional,
    )

    if not plano:
        return 1

    return plano.limite_fotos
