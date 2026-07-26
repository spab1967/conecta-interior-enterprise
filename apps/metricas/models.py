from django.db import models

from apps.empresas.models import Empresa
from apps.profissionais.models import Profissional


class EventoContato(models.Model):

    TIPO_WHATSAPP = "whatsapp"
    TIPO_TELEFONE = "telefone"
    TIPO_SITE = "site"
    TIPO_INSTAGRAM = "instagram"
    TIPO_EMAIL = "email"

    TIPOS = [
        (TIPO_WHATSAPP, "WhatsApp"),
        (TIPO_TELEFONE, "Telefone"),
        (TIPO_SITE, "Site"),
        (TIPO_INSTAGRAM, "Instagram"),
        (TIPO_EMAIL, "E-mail"),
    ]

    empresa = models.ForeignKey(
        Empresa,
        on_delete=models.CASCADE,
        related_name="eventos_contato",
        null=True,
        blank=True,
    )

    profissional = models.ForeignKey(
        Profissional,
        on_delete=models.CASCADE,
        related_name="eventos_contato",
        null=True,
        blank=True,
    )

    tipo = models.CharField(
        max_length=20,
        choices=TIPOS,
    )

    criado_em = models.DateTimeField(
        auto_now_add=True,
        db_index=True,
    )

    class Meta:
        ordering = [
            "-criado_em",
        ]

        verbose_name = "Evento de contato"
        verbose_name_plural = "Eventos de contato"

    def __str__(self):

        destino = (
            self.empresa
            or self.profissional
        )

        return (
            f"{self.get_tipo_display()} - "
            f"{destino}"
        )