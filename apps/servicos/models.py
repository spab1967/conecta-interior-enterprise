from django.core.exceptions import ValidationError
from django.db import models
from django.db.models import Q

from apps.cidades.models import Cidade
from apps.empresas.models import Empresa
from apps.profissionais.models import Profissional


class Servico(models.Model):

    cidade = models.ForeignKey(
        Cidade,
        on_delete=models.CASCADE,
        related_name="servicos",
    )

    empresa = models.ForeignKey(
        Empresa,
        on_delete=models.CASCADE,
        related_name="servicos",
        null=True,
        blank=True,
    )

    profissional = models.ForeignKey(
        Profissional,
        on_delete=models.CASCADE,
        related_name="servicos",
        null=True,
        blank=True,
    )

    nome = models.CharField(max_length=200)

    valor = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        null=True,
        blank=True,
    )

    ativo = models.BooleanField(default=True)

    class Meta:
        ordering = ["nome"]
        verbose_name = "Serviço"
        verbose_name_plural = "Serviços"
        constraints = [
            models.CheckConstraint(
                condition=(
                    Q(empresa__isnull=False, profissional__isnull=True)
                    | Q(empresa__isnull=True, profissional__isnull=False)
                ),
                name="servico_um_titular",
            ),
        ]

    def clean(self):
        super().clean()

        if self.empresa and self.profissional:
            raise ValidationError(
                "O serviço deve pertencer a uma empresa "
                "ou a um profissional, nunca aos dois."
            )

        if not self.empresa and not self.profissional:
            raise ValidationError(
                "Informe a empresa ou o profissional responsável."
            )

    def save(self, *args, **kwargs):
        if self.empresa:
            self.cidade = self.empresa.cidade
        elif self.profissional:
            self.cidade = self.profissional.cidade
        super().save(*args, **kwargs)

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
        return self.nome
