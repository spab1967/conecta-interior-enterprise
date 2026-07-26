from datetime import timedelta

from django.core.management.base import BaseCommand
from django.utils import timezone

from apps.financeiro.services import gerar_pedido_renovacao
from apps.planos.models import Assinatura


class Command(BaseCommand):

    help = (
        "Gera pedidos de renovação automática para assinaturas "
        "ativas próximas do vencimento."
    )

    def add_arguments(self, parser):

        parser.add_argument(
            "--dias",
            type=int,
            default=7,
            help=(
                "Quantidade de dias antes do vencimento "
                "para gerar a cobrança. Padrão: 7."
            ),
        )

    def handle(self, *args, **options):

        dias = options["dias"]

        hoje = timezone.localdate()

        limite = hoje + timedelta(
            days=dias
        )

        assinaturas = (
            Assinatura.objects
            .select_related(
                "plano",
                "empresa",
                "profissional",
            )
            .filter(
                status=Assinatura.STATUS_ATIVA,
                renovacao_automatica=True,
                vencimento__isnull=False,
                vencimento__gte=hoje,
                vencimento__lte=limite,
            )
        )

        processados = 0

        for assinatura in assinaturas:

            pedido = gerar_pedido_renovacao(
                assinatura
            )

            if pedido is not None:
                processados += 1

        self.stdout.write(
            self.style.SUCCESS(
                f"Processamento concluído. "
                f"Assinaturas automáticas analisadas: "
                f"{assinaturas.count()}. "
                f"Pedidos processados: "
                f"{processados}."
            )
        )