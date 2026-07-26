from django.contrib import admin, messages
from django.db import transaction
from django.utils import timezone

from apps.empresas.models import Empresa
from apps.planos.models import Assinatura
from apps.planos.vigencia import calcular_vencimento_plano
from apps.profissionais.models import Profissional

from .models import SolicitacaoCadastro


@admin.register(SolicitacaoCadastro)
class SolicitacaoCadastroAdmin(admin.ModelAdmin):

    list_display = (
        "id",
        "nome",
        "tipo",
        "cidade",
        "categoria",
        "plano",
        "status",
        "criado_em",
    )

    list_filter = (
        "tipo",
        "status",
        "plano",
        "cidade",
        "categoria",
    )

    search_fields = (
        "nome",
        "responsavel",
        "telefone",
        "whatsapp",
        "email",
        "bairro",
        "plano__nome",
    )

    readonly_fields = (
        "criado_em",
        "atualizado_em",
    )

    ordering = (
        "-criado_em",
    )

    actions = (
        "aprovar_e_publicar",
        "marcar_como_recusada",
    )

    fieldsets = (
        (
            "Solicitação",
            {
                "fields": (
                    "plano",
                    "tipo",
                    "nome",
                    "responsavel",
                    "cidade",
                    "categoria",
                    "especialidade",
                    "descricao",
                )
            },
        ),
        (
            "Contato e localização",
            {
                "fields": (
                    "endereco",
                    "bairro",
                    "telefone",
                    "whatsapp",
                    "email",
                    "instagram",
                    "site",
                    "horario",
                )
            },
        ),
        (
            "Moderação",
            {
                "fields": (
                    "status",
                    "observacao_admin",
                )
            },
        ),
        (
            "Controle",
            {
                "fields": (
                    "criado_em",
                    "atualizado_em",
                )
            },
        ),
    )

    @admin.action(
        description="Aprovar, publicar e ativar plano"
    )
    def aprovar_e_publicar(
        self,
        request,
        queryset,
    ):

        aprovadas = 0
        ignoradas = 0
        erros = 0

        for solicitacao in queryset:

            if (
                solicitacao.status
                == SolicitacaoCadastro.STATUS_APROVADO
            ):
                ignoradas += 1
                continue

            try:

                with transaction.atomic():

                    if not solicitacao.plano:
                        raise ValueError(
                            "A solicitação não possui "
                            "um plano selecionado."
                        )

                    if not solicitacao.plano.ativo:
                        raise ValueError(
                            "O plano selecionado está inativo."
                        )

                    empresa = None
                    profissional = None

                    if (
                        solicitacao.tipo
                        == SolicitacaoCadastro.TIPO_EMPRESA
                    ):

                        empresa = self._criar_empresa(
                            solicitacao
                        )

                    elif (
                        solicitacao.tipo
                        == SolicitacaoCadastro.TIPO_PROFISSIONAL
                    ):

                        profissional = (
                            self._criar_profissional(
                                solicitacao
                            )
                        )

                    else:

                        raise ValueError(
                            "Tipo de solicitação inválido."
                        )

                    self._criar_assinatura(
                        solicitacao=solicitacao,
                        empresa=empresa,
                        profissional=profissional,
                    )

                    solicitacao.status = (
                        SolicitacaoCadastro.STATUS_APROVADO
                    )

                    solicitacao.save(
                        update_fields=[
                            "status",
                            "atualizado_em",
                        ]
                    )

                    aprovadas += 1

            except Exception as erro:

                erros += 1

                self.message_user(
                    request,
                    (
                        f"Não foi possível aprovar "
                        f"'{solicitacao.nome}': {erro}"
                    ),
                    level=messages.ERROR,
                )

        if aprovadas:

            self.message_user(
                request,
                (
                    f"{aprovadas} solicitação(ões) "
                    f"aprovada(s), publicada(s) e "
                    f"com plano ativado com sucesso."
                ),
                level=messages.SUCCESS,
            )

        if ignoradas:

            self.message_user(
                request,
                (
                    f"{ignoradas} solicitação(ões) "
                    f"já estavam aprovadas e não "
                    f"foram processadas novamente."
                ),
                level=messages.WARNING,
            )

        if erros:

            self.message_user(
                request,
                (
                    f"{erros} solicitação(ões) "
                    f"apresentaram erro e permaneceram "
                    f"sem aprovação."
                ),
                level=messages.ERROR,
            )

    @admin.action(
        description="Marcar selecionadas como recusadas"
    )
    def marcar_como_recusada(
        self,
        request,
        queryset,
    ):

        atualizadas = (
            queryset
            .exclude(
                status=SolicitacaoCadastro.STATUS_APROVADO
            )
            .update(
                status=SolicitacaoCadastro.STATUS_RECUSADO
            )
        )

        self.message_user(
            request,
            (
                f"{atualizadas} solicitação(ões) "
                f"marcada(s) como recusada(s)."
            ),
            level=messages.SUCCESS,
        )

    def _criar_empresa(
        self,
        solicitacao,
    ):

        if not solicitacao.categoria:

            raise ValueError(
                "A empresa precisa possuir uma categoria."
            )

        existente = (
            Empresa.objects
            .filter(
                cidade=solicitacao.cidade,
                nome_fantasia__iexact=(
                    solicitacao.nome.strip()
                ),
            )
            .first()
        )

        if existente:

            raise ValueError(
                "Já existe uma empresa com esse "
                "nome nesta cidade."
            )

        empresa = Empresa.objects.create(
            cidade=solicitacao.cidade,
            categoria=solicitacao.categoria,
            nome_fantasia=solicitacao.nome.strip(),
            descricao=solicitacao.descricao,
            endereco=solicitacao.endereco,
            bairro=solicitacao.bairro,
            telefone=solicitacao.telefone,
            whatsapp=solicitacao.whatsapp,
            email=solicitacao.email,
            instagram=solicitacao.instagram,
            site=solicitacao.site,
            horario=solicitacao.horario,
            destaque=False,
            ativa=True,
        )

        return empresa

    def _criar_profissional(
        self,
        solicitacao,
    ):

        existente = (
            Profissional.objects
            .filter(
                cidade=solicitacao.cidade,
                nome__iexact=(
                    solicitacao.nome.strip()
                ),
            )
            .first()
        )

        if existente:

            raise ValueError(
                "Já existe um profissional com esse "
                "nome nesta cidade."
            )

        profissional = Profissional.objects.create(
            cidade=solicitacao.cidade,
            categoria=solicitacao.categoria,
            nome=solicitacao.nome.strip(),
            especialidade=solicitacao.especialidade,
            descricao=solicitacao.descricao,
            endereco=solicitacao.endereco,
            bairro=solicitacao.bairro,
            telefone=solicitacao.telefone,
            whatsapp=solicitacao.whatsapp,
            email=solicitacao.email,
            instagram=solicitacao.instagram,
            site=solicitacao.site,
            horario=solicitacao.horario,
            atendimento_domiciliar=False,
            destaque=False,
            ativo=True,
        )

        return profissional

    def _criar_assinatura(
        self,
        solicitacao,
        empresa=None,
        profissional=None,
    ):

        if empresa:

            assinatura_existente = (
                Assinatura.objects
                .filter(
                    empresa=empresa,
                    status=Assinatura.STATUS_ATIVA,
                )
                .first()
            )

        elif profissional:

            assinatura_existente = (
                Assinatura.objects
                .filter(
                    profissional=profissional,
                    status=Assinatura.STATUS_ATIVA,
                )
                .first()
            )

        else:

            raise ValueError(
                "Não foi possível identificar "
                "o titular da assinatura."
            )

        if assinatura_existente:

            raise ValueError(
                "O cadastro já possui uma "
                "assinatura ativa."
            )

        inicio = timezone.localdate()

        vencimento = calcular_vencimento_plano(
            plano=solicitacao.plano,
            inicio=inicio,
        )

        assinatura = Assinatura(
            plano=solicitacao.plano,
            empresa=empresa,
            profissional=profissional,
            status=Assinatura.STATUS_ATIVA,
            inicio=inicio,
            vencimento=vencimento,
            renovacao_automatica=False,
            observacoes=(
                "Assinatura criada automaticamente "
                f"a partir da solicitação de cadastro "
                f"#{solicitacao.pk}."
            ),
        )

        assinatura.full_clean()
        assinatura.save()

        return assinatura