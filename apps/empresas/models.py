from urllib.parse import quote

from django.conf import settings
from django.db import models
from django.utils.text import slugify

from apps.cidades.models import Cidade
from apps.categorias.models import Categoria


class Empresa(models.Model):

    usuario = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="empresas_conecta",
        verbose_name="Usuário responsável",
    )

    cidade = models.ForeignKey(
        Cidade,
        on_delete=models.PROTECT,
        related_name="empresas",
    )

    categoria = models.ForeignKey(
        Categoria,
        on_delete=models.PROTECT,
        related_name="empresas",
    )

    nome_fantasia = models.CharField(
        max_length=160,
    )

    slug = models.SlugField(
        max_length=180,
        blank=True,
    )

    descricao = models.TextField(
        blank=True,
    )

    endereco = models.CharField(
        max_length=220,
        blank=True,
    )

    bairro = models.CharField(
        max_length=100,
        blank=True,
    )

    telefone = models.CharField(
        max_length=30,
        blank=True,
    )

    whatsapp = models.CharField(
        max_length=30,
        blank=True,
    )

    email = models.EmailField(
        blank=True,
    )

    instagram = models.URLField(
        blank=True,
    )

    site = models.URLField(
        blank=True,
    )

    horario = models.CharField(
        max_length=180,
        blank=True,
    )

    logo = models.ImageField(
        upload_to="empresas/logos/",
        blank=True,
        null=True,
    )

    destaque = models.BooleanField(
        default=False,
    )

    ativa = models.BooleanField(
        default=True,
    )

    liberacao_financeira_ativa = models.BooleanField(default=False)
    liberacao_financeira_ate = models.DateField(null=True, blank=True)
    liberacao_financeira_motivo = models.CharField(max_length=255, blank=True)
    liberacao_financeira_observacao = models.TextField(blank=True)
    liberacao_financeira_por = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="+",
    )
    liberacao_financeira_em = models.DateTimeField(null=True, blank=True)

    criada_em = models.DateTimeField(
        auto_now_add=True,
    )

    atualizada_em = models.DateTimeField(
        auto_now=True,
    )

    class Meta:
        ordering = [
            "-destaque",
            "nome_fantasia",
        ]

        constraints = [
            models.UniqueConstraint(
                fields=[
                    "cidade",
                    "slug",
                ],
                name="empresa_slug_unico_por_cidade",
            )
        ]

        verbose_name = "Empresa"
        verbose_name_plural = "Empresas"

    def save(self, *args, **kwargs):

        if not self.slug:

            base = slugify(
                self.nome_fantasia
            )

            slug = base
            indice = 2

            while (
                Empresa.objects.filter(
                    cidade=self.cidade,
                    slug=slug,
                )
                .exclude(pk=self.pk)
                .exists()
            ):
                slug = f"{base}-{indice}"
                indice += 1

            self.slug = slug

        super().save(*args, **kwargs)

    @property
    def whatsapp_link(self):

        numero = "".join(
            filter(
                str.isdigit,
                self.whatsapp or "",
            )
        )

        if numero and not numero.startswith("55"):
            numero = f"55{numero}"

        if not numero:
            return ""

        mensagem = (
            f"Olá! Encontrei a empresa "
            f"{self.nome_fantasia} no Conecta Interior "
            f"e gostaria de mais informações."
        )

        mensagem_codificada = quote(
            mensagem
        )

        return (
            f"https://wa.me/{numero}"
            f"?text={mensagem_codificada}"
        )

    def __str__(self):

        return (
            f"{self.nome_fantasia} — "
            f"{self.cidade.nome}"
        )


class FotoEmpresa(models.Model):

    empresa = models.ForeignKey(
        Empresa,
        on_delete=models.CASCADE,
        related_name="galeria",
    )

    imagem = models.ImageField(
        upload_to="empresas/galeria/",
    )

    ordem = models.PositiveIntegerField(
        default=0,
    )

    criada_em = models.DateTimeField(
        auto_now_add=True,
    )

    class Meta:
        ordering = [
            "ordem",
            "id",
        ]

        verbose_name = "Foto da empresa"
        verbose_name_plural = "Fotos da empresa"

    def __str__(self):
        return f"Foto de {self.empresa.nome_fantasia}"
