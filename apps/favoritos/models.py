from django.db import models

from apps.empresas.models import Empresa
from apps.profissionais.models import Profissional


class Favorito(models.Model):

    identificador = models.CharField(
        "identificador do visitante",
        max_length=100,
        db_index=True,
    )

    empresa = models.ForeignKey(
        Empresa,
        on_delete=models.CASCADE,
        related_name="favoritos",
        null=True,
        blank=True,
    )

    profissional = models.ForeignKey(
        Profissional,
        on_delete=models.CASCADE,
        related_name="favoritos",
        null=True,
        blank=True,
    )

    criado_em = models.DateTimeField(
        "adicionado em",
        auto_now_add=True,
    )

    class Meta:

        ordering = [
            "-criado_em",
        ]

        verbose_name = "Favorito"
        verbose_name_plural = "Favoritos"

        constraints = [

            models.UniqueConstraint(
                fields=[
                    "identificador",
                    "empresa",
                ],
                name="favorito_empresa_unico",
            ),

            models.UniqueConstraint(
                fields=[
                    "identificador",
                    "profissional",
                ],
                name="favorito_profissional_unico",
            ),

        ]

    def __str__(self):

        if self.empresa:
            return f"{self.identificador} - {self.empresa}"

        if self.profissional:
            return f"{self.identificador} - {self.profissional}"

        return self.identificador