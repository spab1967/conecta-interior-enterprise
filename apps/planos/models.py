from datetime import timedelta

from django.core.exceptions import ValidationError
from django.db import models
from django.utils import timezone

from apps.empresas.models import Empresa
from apps.profissionais.models import Profissional


class Plano(models.Model):

    nome = models.CharField(
        max_length=100,
        unique=True,
    )

    descricao = models.TextField(
        blank=True,
    )

    preco_mensal = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=0,
    )

    destaque_busca = models.BooleanField(
        default=False,
    )

    destaque_perfil = models.BooleanField(
        default=False,
    )

    acesso_metricas = models.BooleanField(
        default=False,
    )

    prioridade_resultados = models.BooleanField(
        default=False,
    )

    selo_destaque = models.BooleanField(
        default=False,
    )

    limite_fotos = models.PositiveIntegerField(
        default=1,
    )

    ordem = models.PositiveIntegerField(
        default=0,
    )

    ativo = models.BooleanField(
        default=True,
    )

    criado_em = models.DateTimeField(
        auto_now_add=True,
    )

    atualizado_em = models.DateTimeField(
        auto_now=True,
    )

    class Meta:
        ordering = (
            "ordem",
            "preco_mensal",
            "nome",
        )

        verbose_name = "Plano"
        verbose_name_plural = "Planos"

    def __str__(self):
        return self.nome


class Assinatura(models.Model):

    STATUS_ATIVA = "ativa"
    STATUS_PENDENTE = "pendente"
    STATUS_CANCELADA = "cancelada"
    STATUS_VENCIDA = "vencida"

    STATUS_CHOICES = (
        (
            STATUS_ATIVA,
            "Ativa",
        ),
        (
            STATUS_PENDENTE,
            "Pendente",
        ),
        (
            STATUS_CANCELADA,
            "Cancelada",
        ),
        (
            STATUS_VENCIDA,
            "Vencida",
        ),
    )

    plano = models.ForeignKey(
        Plano,
        on_delete=models.PROTECT,
        related_name="assinaturas",
    )

    empresa = models.ForeignKey(
        Empresa,
        on_delete=models.CASCADE,
        related_name="assinaturas",
        null=True,
        blank=True,
    )

    profissional = models.ForeignKey(
        Profissional,
        on_delete=models.CASCADE,
        related_name="assinaturas",
        null=True,
        blank=True,
    )

    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default=STATUS_ATIVA,
    )

    inicio = models.DateField(
        default=timezone.localdate,
    )

    vencimento = models.DateField(
        null=True,
        blank=True,
    )

    renovacao_automatica = models.BooleanField(
        default=False,
    )

    observacoes = models.TextField(
        blank=True,
    )

    criada_em = models.DateTimeField(
        auto_now_add=True,
    )

    atualizada_em = models.DateTimeField(
        auto_now=True,
    )

    class Meta:
        ordering = (
            "-inicio",
            "-criada_em",
        )

        verbose_name = "Assinatura"
        verbose_name_plural = "Assinaturas"

    def clean(self):

        super().clean()

        if self.empresa and self.profissional:
            raise ValidationError(
                "A assinatura deve pertencer a uma empresa "
                "ou a um profissional, nunca aos dois."
            )

        if not self.empresa and not self.profissional:
            raise ValidationError(
                "Informe a empresa ou o profissional "
                "responsável pela assinatura."
            )

        if (
            self.vencimento
            and self.inicio
            and self.vencimento < self.inicio
        ):
            raise ValidationError(
                {
                    "vencimento":
                        "O vencimento não pode ser anterior "
                        "ao início da assinatura."
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

    @property
    def esta_vigente(self):

        if self.status != self.STATUS_ATIVA:
            return False

        hoje = timezone.localdate()

        if self.inicio > hoje:
            return False

        if self.plano.preco_mensal <= 0:
            return True

        if (
            self.vencimento
            and self.vencimento + timedelta(days=7) < hoje
        ):
            return False

        return True

    def __str__(self):
        return (
            f"{self.titular} — "
            f"{self.plano.nome}"
        )
