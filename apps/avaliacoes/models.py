from django.db import models

from apps.empresas.models import Empresa
from apps.profissionais.models import Profissional


class Avaliacao(models.Model):

    empresa = models.ForeignKey(
        Empresa,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name="avaliacoes",
    )

    profissional = models.ForeignKey(
        Profissional,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name="avaliacoes",
    )

    nome = models.CharField(
        max_length=120,
    )

    nota = models.PositiveSmallIntegerField()

    comentario = models.TextField()

    aprovado = models.BooleanField(
        default=False,
    )

    criado_em = models.DateTimeField(
        auto_now_add=True,
    )

    class Meta:

        ordering = [
            "-criado_em",
        ]

    def __str__(self):

        if self.empresa:

            return f"{self.nome} - {self.empresa}"

        return f"{self.nome} - {self.profissional}"