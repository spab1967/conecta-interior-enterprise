from django.core.exceptions import ValidationError
from django.db import models
from django.utils import timezone

from apps.empresas.models import Empresa
from apps.planos.models import Assinatura, Plano
from apps.profissionais.models import Profissional


class PedidoFinanceiro(models.Model):

    STATUS_PENDENTE = "pendente"
    STATUS_PAGO = "pago"
    STATUS_CANCELADO = "cancelado"

    STATUS_CHOICES = (
        (
            STATUS_PENDENTE,
            "Pendente",
        ),
        (
            STATUS_PAGO,
            "Pago",
        ),
        (
            STATUS_CANCELADO,
            "Cancelado",
        ),
    )

    empresa = models.ForeignKey(
        Empresa,
        on_delete=models.CASCADE,
        related_name="pedidos_financeiros",
        null=True,
        blank=True,
    )

    profissional = models.ForeignKey(
        Profissional,
        on_delete=models.CASCADE,
        related_name="pedidos_financeiros",
        null=True,
        blank=True,
    )

    plano = models.ForeignKey(
        Plano,
        on_delete=models.PROTECT,
        related_name="pedidos_financeiros",
    )

    assinatura = models.ForeignKey(
        Assinatura,
        on_delete=models.SET_NULL,
        related_name="pedidos_financeiros",
        null=True,
        blank=True,
    )

    valor = models.DecimalField(
        max_digits=10,
        decimal_places=2,
    )

    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default=STATUS_PENDENTE,
    )

    observacoes = models.TextField(
        blank=True,
    )

    criado_em = models.DateTimeField(
        auto_now_add=True,
    )

    atualizado_em = models.DateTimeField(
        auto_now=True,
    )

    class Meta:
        ordering = (
            "-criado_em",
        )

        verbose_name = "Pedido Financeiro"
        verbose_name_plural = "Pedidos Financeiros"

    def clean(self):

        super().clean()

        if self.empresa and self.profissional:
            raise ValidationError(
                "O pedido deve pertencer a uma empresa "
                "ou a um profissional, nunca aos dois."
            )

        if not self.empresa and not self.profissional:
            raise ValidationError(
                "Informe a empresa ou o profissional "
                "responsável pelo pedido."
            )

        if self.assinatura:

            if (
                self.empresa
                and self.assinatura.empresa_id
                != self.empresa_id
            ):
                raise ValidationError(
                    {
                        "assinatura":
                            "A assinatura não pertence "
                            "à empresa deste pedido."
                    }
                )

            if (
                self.profissional
                and self.assinatura.profissional_id
                != self.profissional_id
            ):
                raise ValidationError(
                    {
                        "assinatura":
                            "A assinatura não pertence "
                            "ao profissional deste pedido."
                    }
                )

    @property
    def titular(self):

        if self.empresa:
            return self.empresa.nome_fantasia

        if self.profissional:
            return self.profissional.nome

        return "-"

    @property
    def tipo_titular(self):

        if self.empresa:
            return "Empresa"

        if self.profissional:
            return "Profissional"

        return "-"

    def __str__(self):

        identificador = (
            self.pk
            if self.pk
            else "novo"
        )

        return (
            f"Pedido #{identificador} — "
            f"{self.titular} — "
            f"{self.plano.nome}"
        )


class Pagamento(models.Model):

    TIPO_PIX = "pix"
    TIPO_CARTAO = "cartao"
    TIPO_BOLETO = "boleto"
    TIPO_MANUAL = "manual"

    TIPO_CHOICES = (
        (
            TIPO_PIX,
            "PIX",
        ),
        (
            TIPO_CARTAO,
            "Cartão",
        ),
        (
            TIPO_BOLETO,
            "Boleto",
        ),
        (
            TIPO_MANUAL,
            "Manual",
        ),
    )

    STATUS_PENDENTE = "pendente"
    STATUS_APROVADO = "aprovado"
    STATUS_RECUSADO = "recusado"
    STATUS_ESTORNADO = "estornado"

    STATUS_CHOICES = (
        (
            STATUS_PENDENTE,
            "Pendente",
        ),
        (
            STATUS_APROVADO,
            "Aprovado",
        ),
        (
            STATUS_RECUSADO,
            "Recusado",
        ),
        (
            STATUS_ESTORNADO,
            "Estornado",
        ),
    )

    pedido = models.ForeignKey(
        PedidoFinanceiro,
        on_delete=models.CASCADE,
        related_name="pagamentos",
    )

    tipo = models.CharField(
        max_length=20,
        choices=TIPO_CHOICES,
        default=TIPO_PIX,
    )

    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default=STATUS_PENDENTE,
    )

    valor = models.DecimalField(
        max_digits=10,
        decimal_places=2,
    )

    codigo_transacao = models.CharField(
        max_length=200,
        blank=True,
    )
    
    comprovante = models.FileField(
        upload_to="comprovantes/%Y/%m/",
        null=True,
        blank=True,
    )

    pago_em = models.DateTimeField(
        null=True,
        blank=True,
    )

    criado_em = models.DateTimeField(
        auto_now_add=True,
    )

    atualizado_em = models.DateTimeField(
        auto_now=True,
    )

    class Meta:
        ordering = (
            "-criado_em",
        )

        verbose_name = "Pagamento"
        verbose_name_plural = "Pagamentos"

    def clean(self):

        super().clean()

        if (
            self.valor is not None
            and self.pedido_id
            and self.valor != self.pedido.valor
        ):
            raise ValidationError(
                {
                    "valor":
                        "O valor do pagamento deve ser "
                        "igual ao valor do pedido."
                }
            )

    def marcar_como_pago(self):

        self.status = self.STATUS_APROVADO
        self.pago_em = timezone.now()

        self.save(
            update_fields=[
                "status",
                "pago_em",
                "atualizado_em",
            ]
        )

    def __str__(self):

        identificador = (
            self.pk
            if self.pk
            else "novo"
        )

        return (
            f"Pagamento #{identificador} — "
            f"{self.pedido.titular}"
        )