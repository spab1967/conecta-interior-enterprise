from urllib.parse import quote

from django.conf import settings
from django.db import models
from django.utils.text import slugify

from apps.cidades.models import Cidade
from apps.categorias.models import Categoria
from apps.empresas.models import Empresa


class Profissional(models.Model):

    usuario = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="profissionais_conecta",
        verbose_name="Usuário responsável",
    )

    cidade = models.ForeignKey(
        Cidade,
        on_delete=models.PROTECT,
        related_name="profissionais",
    )

    categoria = models.ForeignKey(
        Categoria,
        on_delete=models.PROTECT,
        related_name="profissionais",
        null=True,
        blank=True,
    )

    empresa = models.ForeignKey(
        Empresa,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="profissionais",
    )

    nome = models.CharField(
        max_length=180,
    )

    slug = models.SlugField(
        max_length=180,
        blank=True,
    )

    especialidade = models.CharField(
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
        max_length=120,
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

    foto = models.ImageField(
        upload_to="profissionais/",
        blank=True,
        null=True,
    )

    atendimento_domiciliar = models.BooleanField(
        default=False,
    )

    destaque = models.BooleanField(
        default=False,
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
        ordering = [
            "-destaque",
            "nome",
        ]

        constraints = [
            models.UniqueConstraint(
                fields=[
                    "cidade",
                    "slug",
                ],
                name="profissional_slug_unico",
            )
        ]

        verbose_name = "Profissional"
        verbose_name_plural = "Profissionais"

    def save(self, *args, **kwargs):

        if not self.slug:

            base = slugify(
                self.nome
            )

            slug = base
            indice = 2

            while (
                Profissional.objects.filter(
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
            f"Olá! Encontrei o perfil de "
            f"{self.nome} no Conecta Interior "
            f"e gostaria de informações sobre seus serviços."
        )

        mensagem_codificada = quote(
            mensagem
        )

        return (
            f"https://wa.me/{numero}"
            f"?text={mensagem_codificada}"
        )

    def __str__(self):

        if self.empresa:

            return (
                f"{self.nome} - "
                f"{self.empresa.nome_fantasia}"
            )

        return self.nome


class FotoProfissional(models.Model):

    profissional = models.ForeignKey(
        Profissional,
        on_delete=models.CASCADE,
        related_name="galeria",
    )

    imagem = models.ImageField(
        upload_to="profissionais/galeria/",
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

        verbose_name = "Foto do profissional"
        verbose_name_plural = "Fotos do profissional"

    def __str__(self):
        return f"Foto de {self.profissional.nome}"

