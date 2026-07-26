from django.db import models
from django.utils.text import slugify


class Cidade(models.Model):
    nome = models.CharField("nome", max_length=120)
    estado = models.CharField("UF", max_length=2, default="MG")
    slug = models.SlugField("endereço amigável", max_length=140, unique=True, blank=True)

    cep_principal = models.CharField("CEP principal", max_length=9, blank=True)
    ddd = models.CharField("DDD", max_length=3, blank=True)
    populacao = models.PositiveIntegerField("população", null=True, blank=True)
    latitude = models.DecimalField(
        "latitude", max_digits=10, decimal_places=7, null=True, blank=True
    )
    longitude = models.DecimalField(
        "longitude", max_digits=10, decimal_places=7, null=True, blank=True
    )

    telefone_util = models.CharField("telefone útil", max_length=30, blank=True)
    site_prefeitura = models.URLField("site da prefeitura", blank=True)

    descricao = models.TextField("descrição da cidade", blank=True)
    imagem = models.ImageField(
        "imagem da cidade", upload_to="cidades/imagens/", blank=True, null=True
    )
    banner = models.ImageField(
        "banner municipal", upload_to="cidades/banners/", blank=True, null=True
    )

    titulo_seo = models.CharField("título para SEO", max_length=70, blank=True)
    descricao_seo = models.CharField("descrição para SEO", max_length=160, blank=True)

    ativa = models.BooleanField("cidade ativa", default=True)
    criada_em = models.DateTimeField("criada em", auto_now_add=True)
    atualizada_em = models.DateTimeField("atualizada em", auto_now=True)

    class Meta:
        ordering = ["nome"]
        verbose_name = "Cidade"
        verbose_name_plural = "Cidades"

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.nome)

        self.estado = (self.estado or "").upper().strip()

        if not self.titulo_seo:
            self.titulo_seo = f"{self.nome} - Comércio e Serviços Locais"

        if not self.descricao_seo:
            self.descricao_seo = (
                f"Encontre empresas, profissionais, comércio e serviços em "
                f"{self.nome}/{self.estado}."
            )[:160]

        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.nome}/{self.estado}"
