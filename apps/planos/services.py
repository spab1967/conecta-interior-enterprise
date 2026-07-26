from django.utils import timezone

from .models import Assinatura


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

    queryset = queryset.filter(
        vencimento__isnull=True
    ) | queryset.filter(
        vencimento__gte=hoje
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