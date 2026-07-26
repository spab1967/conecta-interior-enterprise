from django.core.validators import MinLengthValidator
from django.db import models

from apps.cidades.models import Cidade
from apps.categorias.models import Categoria
from apps.planos.models import Plano


class SolicitacaoCadastro(models.Model):

    TIPO_EMPRESA = "empresa"
    TIPO_PROFISSIONAL = "profissional"

    TIPOS = [
        (TIPO_EMPRESA, "Empresa"),
        (TIPO_PROFISSIONAL, "Profissional"),
    ]

    STATUS_PENDENTE = "pendente"
    STATUS_APROVADO = "aprovado"
    STATUS_RECUSADO = "recusado"

    STATUS = [
        (STATUS_PENDENTE, "Pendente"),
        (STATUS_APROVADO, "Aprovado"),
        (STATUS_RECUSADO, "Recusado"),
    ]

    plano = models.ForeignKey(
        Plano,
        on_delete=models.PROTECT,
        related_name="solicitacoes_cadastro",
        null=True,
        blank=True,
        verbose_name="plano solicitado",
    )

    tipo = models.CharField(
        "tipo de cadastro",
        max_length=20,
        choices=TIPOS,
    )

    nome = models.CharField(
        "nome / nome da empresa",
        max_length=180,
    )

    responsavel = models.CharField(
        "responsável",
        max_length=180,
        blank=True,
    )

    cidade = models.ForeignKey(
        Cidade,
        on_delete=models.PROTECT,
        related_name="solicitacoes_cadastro",
    )

    categoria = models.ForeignKey(
        Categoria,
        on_delete=models.PROTECT,
        related_name="solicitacoes_cadastro",
        null=True,
        blank=True,
    )

    especialidade = models.CharField(
        "especialidade",
        max_length=180,
        blank=True,
    )

    descricao = models.TextField(
        "descrição",
        blank=True,
        validators=[
            MinLengthValidator(10),
        ],
    )

    endereco = models.CharField(
        "endereço",
        max_length=220,
        blank=True,
    )

    bairro = models.CharField(
        "bairro",
        max_length=120,
        blank=True,
    )

    telefone = models.CharField(
        "telefone",
        max_length=30,
        blank=True,
    )

    whatsapp = models.CharField(
        "WhatsApp",
        max_length=30,
    )

    email = models.EmailField(
        "e-mail",
        blank=True,
    )

    instagram = models.URLField(
        "Instagram",
        blank=True,
    )

    site = models.URLField(
        "site",
        blank=True,
    )

    horario = models.CharField(
        "horário de atendimento",
        max_length=180,
        blank=True,
    )

    status = models.CharField(
        "status",
        max_length=20,
        choices=STATUS,
        default=STATUS_PENDENTE,
    )

    observacao_admin = models.TextField(
        "observação administrativa",
        blank=True,
    )

    criado_em = models.DateTimeField(
        "enviado em",
        auto_now_add=True,
    )

    atualizado_em = models.DateTimeField(
        "atualizado em",
        auto_now=True,
    )

    class Meta:
        ordering = ["-criado_em"]
        verbose_name = "Solicitação de cadastro"
        verbose_name_plural = "Solicitações de cadastro"

    def __str__(self):

        return (
            f"{self.get_tipo_display()} — "
            f"{self.nome} — "
            f"{self.cidade}"
        )