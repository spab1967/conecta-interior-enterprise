from datetime import timedelta

from django.core.management.base import BaseCommand
from django.db import transaction
from django.utils import timezone

from apps.planos.models import Assinatura
from apps.planos.services import DIAS_TOLERANCIA


class Command(BaseCommand):

    help = (
        "Atualiza automaticamente as vigências "
        "das assinaturas."
    )

    @transaction.atomic
    def handle(self, *args, **options):

        hoje = timezone.localdate()

        assinaturas_vencidas = (
            Assinatura.objects
            .filter(
                status=Assinatura.STATUS_ATIVA,
                vencimento__isnull=False,
                vencimento__lt=hoje - timedelta(days=DIAS_TOLERANCIA),
                plano__preco_mensal__gt=0,
            )
        )

        atualizadas = assinaturas_vencidas.update(
            status=Assinatura.STATUS_VENCIDA
        )

        assinaturas_iniciadas = (
            Assinatura.objects
            .select_related(
                "empresa",
                "profissional",
                "plano",
            )
            .filter(
                status=Assinatura.STATUS_ATIVA,
                inicio__lte=hoje,
            )
        )

        ativacoes_processadas = 0

        for assinatura in assinaturas_iniciadas:

            if assinatura.empresa_id:

                anteriores = (
                    Assinatura.objects
                    .filter(
                        empresa_id=assinatura.empresa_id,
                        status=Assinatura.STATUS_ATIVA,
                        inicio__lt=assinatura.inicio,
                    )
                    .exclude(
                        pk=assinatura.pk
                    )
                )

            else:

                anteriores = (
                    Assinatura.objects
                    .filter(
                        profissional_id=assinatura.profissional_id,
                        status=Assinatura.STATUS_ATIVA,
                        inicio__lt=assinatura.inicio,
                    )
                    .exclude(
                        pk=assinatura.pk
                    )
                )

            quantidade = anteriores.update(
                status=Assinatura.STATUS_VENCIDA
            )

            if quantidade:
                ativacoes_processadas += 1

        self.stdout.write(
            self.style.SUCCESS(
                (
                    f"Processamento concluído. "
                    f"Assinaturas vencidas: {atualizadas}. "
                    f"Transições processadas: "
                    f"{ativacoes_processadas}."
                )
            )
        )
