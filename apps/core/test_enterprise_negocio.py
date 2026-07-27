from decimal import Decimal

from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase
from django.urls import reverse

from apps.avaliacoes.models import Avaliacao
from apps.cadastros.models import SolicitacaoCadastro
from apps.categorias.models import Categoria
from apps.cidades.models import Cidade
from apps.empresas.models import Empresa
from apps.financeiro.models import Pagamento, PedidoFinanceiro
from apps.financeiro.services import aprovar_pagamento
from apps.metricas.models import EventoContato
from apps.planos.models import Assinatura, Plano
from apps.profissionais.models import Profissional


class EnterpriseBusinessFlowTests(TestCase):

    @classmethod
    def setUpTestData(cls):
        User = get_user_model()

        cls.cliente = User.objects.create_user(
            username="cliente_negocio",
            password="Teste@123",
        )

        cls.staff = User.objects.create_user(
            username="staff_negocio",
            password="Teste@123",
            is_staff=True,
        )

        cls.cidade = Cidade.objects.create(
            nome="Cidade Negocio",
            estado="MG",
            slug="cidade-negocio",
        )

        cls.categoria = Categoria.objects.create(
            nome="Categoria Negocio",
            slug="categoria-negocio",
        )

        cls.plano = Plano.objects.create(
            nome="Plano Negocio",
            descricao="Plano para testes",
            preco_mensal=Decimal("39.90"),
            ativo=True,
            ordem=10,
        )

        cls.empresa = Empresa.objects.create(
            usuario=cls.cliente,
            cidade=cls.cidade,
            categoria=cls.categoria,
            nome_fantasia="Empresa Negocio",
            whatsapp="37999999999",
            ativa=True,
        )

        cls.profissional = Profissional.objects.create(
            usuario=cls.cliente,
            cidade=cls.cidade,
            categoria=cls.categoria,
            nome="Profissional Negocio",
            especialidade="Teste",
            whatsapp="37988888888",
            ativo=True,
        )

    def _pedido_empresa(self):
        return PedidoFinanceiro.objects.create(
            empresa=self.empresa,
            profissional=None,
            plano=self.plano,
            valor=self.plano.preco_mensal,
            status=PedidoFinanceiro.STATUS_PENDENTE,
        )

    def _pedido_profissional(self):
        return PedidoFinanceiro.objects.create(
            empresa=None,
            profissional=self.profissional,
            plano=self.plano,
            valor=self.plano.preco_mensal,
            status=PedidoFinanceiro.STATUS_PENDENTE,
        )

    def test_aprovar_pagamento_empresa_cria_assinatura(self):
        pedido = self._pedido_empresa()

        pagamento = Pagamento.objects.create(
            pedido=pedido,
            tipo=Pagamento.TIPO_PIX,
            status=Pagamento.STATUS_PENDENTE,
            valor=pedido.valor,
        )

        aprovar_pagamento(pagamento)

        pedido.refresh_from_db()
        pagamento.refresh_from_db()

        self.assertEqual(
            pagamento.status,
            Pagamento.STATUS_APROVADO,
        )

        self.assertEqual(
            pedido.status,
            PedidoFinanceiro.STATUS_PAGO,
        )

        self.assertIsNotNone(
            pedido.assinatura_id
        )

        self.assertEqual(
            pedido.assinatura.empresa_id,
            self.empresa.pk,
        )

        self.assertEqual(
            pedido.assinatura.plano_id,
            self.plano.pk,
        )

    def test_aprovar_pagamento_profissional_cria_assinatura(self):
        pedido = self._pedido_profissional()

        pagamento = Pagamento.objects.create(
            pedido=pedido,
            tipo=Pagamento.TIPO_PIX,
            status=Pagamento.STATUS_PENDENTE,
            valor=pedido.valor,
        )

        aprovar_pagamento(pagamento)

        pedido.refresh_from_db()
        pagamento.refresh_from_db()

        self.assertEqual(
            pagamento.status,
            Pagamento.STATUS_APROVADO,
        )

        self.assertEqual(
            pedido.status,
            PedidoFinanceiro.STATUS_PAGO,
        )

        self.assertIsNotNone(
            pedido.assinatura_id
        )

        self.assertEqual(
            pedido.assinatura.profissional_id,
            self.profissional.pk,
        )

    def test_aprovar_pagamento_e_idempotente(self):
        pedido = self._pedido_empresa()

        pagamento = Pagamento.objects.create(
            pedido=pedido,
            tipo=Pagamento.TIPO_PIX,
            status=Pagamento.STATUS_PENDENTE,
            valor=pedido.valor,
        )

        aprovar_pagamento(pagamento)

        primeira = Assinatura.objects.count()

        pagamento.refresh_from_db()

        aprovar_pagamento(pagamento)

        self.assertEqual(
            Assinatura.objects.count(),
            primeira,
        )

    def test_pagamento_empresa_exige_proprietario(self):
        pedido = self._pedido_empresa()

        outro = get_user_model().objects.create_user(
            username="intruso_financeiro",
            password="Teste@123",
        )

        self.client.force_login(outro)

        response = self.client.get(
            reverse(
                "financeiro:pagamento",
                kwargs={
                    "pedido_id": pedido.pk,
                },
            )
        )

        self.assertEqual(
            response.status_code,
            404,
        )

    def test_pagamento_empresa_proprietario_acessa(self):
        pedido = self._pedido_empresa()

        self.client.force_login(
            self.cliente
        )

        response = self.client.get(
            reverse(
                "financeiro:pagamento",
                kwargs={
                    "pedido_id": pedido.pk,
                },
            )
        )

        self.assertEqual(
            response.status_code,
            200,
        )

    def test_confirmar_pagamento_via_interface(self):
        pedido = self._pedido_empresa()

        pagamento = Pagamento.objects.create(
            pedido=pedido,
            tipo=Pagamento.TIPO_PIX,
            status=Pagamento.STATUS_PENDENTE,
            valor=pedido.valor,
        )

        comprovante = SimpleUploadedFile(
            "comprovante_teste.pdf",
            b"%PDF-1.4 comprovante de teste",
            content_type="application/pdf",
        )

        self.client.force_login(
            self.cliente
        )

        response = self.client.post(
            reverse(
                "financeiro:confirmar",
                kwargs={
                    "pagamento_id": pagamento.pk,
                },
            ),
            {
                "comprovante": comprovante,
            },
        )

        self.assertEqual(
            response.status_code,
            302,
        )

        pedido.refresh_from_db()
        pagamento.refresh_from_db()

        self.assertTrue(
            bool(pagamento.comprovante)
        )

        self.assertEqual(
            pagamento.status,
            Pagamento.STATUS_PENDENTE,
        )

        self.assertEqual(
            pedido.status,
            PedidoFinanceiro.STATUS_PENDENTE,
        )

        self.assertIsNone(
            pedido.assinatura_id
        )

        self.client.force_login(
            self.staff
        )

        response = self.client.post(
            reverse(
                "administracao:aprovar_pagamento",
                kwargs={
                    "pagamento_id": pagamento.pk,
                },
            )
        )

        self.assertEqual(
            response.status_code,
            302,
        )

        pedido.refresh_from_db()
        pagamento.refresh_from_db()

        self.assertEqual(
            pagamento.status,
            Pagamento.STATUS_APROVADO,
        )

        self.assertEqual(
            pedido.status,
            PedidoFinanceiro.STATUS_PAGO,
        )

        self.assertIsNotNone(
            pedido.assinatura_id
        )

        self.assertEqual(
            pedido.assinatura.empresa_id,
            self.empresa.pk,
        )

        self.assertEqual(
            pedido.assinatura.plano_id,
            self.plano.pk,
        )

    def test_historico_financeiro_exige_login(self):
        response = self.client.get(
            reverse(
                "financeiro:historico"
            )
        )

        self.assertEqual(
            response.status_code,
            302,
        )

    def test_historico_financeiro_cliente_responde_200(self):
        self._pedido_empresa()

        self.client.force_login(
            self.cliente
        )

        response = self.client.get(
            reverse(
                "financeiro:historico"
            )
        )

        self.assertEqual(
            response.status_code,
            200,
        )

    def test_contato_whatsapp_empresa_registra_metrica(self):
        response = self.client.get(
            reverse(
                "metricas:contato_empresa",
                kwargs={
                    "empresa_id": self.empresa.pk,
                    "tipo": "whatsapp",
                },
            )
        )

        self.assertEqual(
            response.status_code,
            302,
        )

        self.assertTrue(
            EventoContato.objects.filter(
                empresa=self.empresa,
                tipo=EventoContato.TIPO_WHATSAPP,
            ).exists()
        )

    def test_contato_whatsapp_profissional_registra_metrica(self):
        response = self.client.get(
            reverse(
                "metricas:contato_profissional",
                kwargs={
                    "profissional_id": self.profissional.pk,
                    "tipo": "whatsapp",
                },
            )
        )

        self.assertEqual(
            response.status_code,
            302,
        )

        self.assertTrue(
            EventoContato.objects.filter(
                profissional=self.profissional,
                tipo=EventoContato.TIPO_WHATSAPP,
            ).exists()
        )

    def test_solicitacao_publica_empresa_e_pendente(self):
        response = self.client.post(
            reverse(
                "cadastros:anuncie"
            ),
            {
                "plano": self.plano.pk,
                "tipo": SolicitacaoCadastro.TIPO_EMPRESA,
                "nome": "Empresa Solicitada",
                "responsavel": "Responsavel Teste",
                "cidade": self.cidade.pk,
                "categoria": self.categoria.pk,
                "especialidade": "",
                "descricao": (
                    "Descricao valida de empresa solicitada."
                ),
                "endereco": "",
                "bairro": "",
                "telefone": "",
                "whatsapp": "37977777777",
                "email": "",
                "instagram": "",
                "site": "",
                "horario": "",
            },
        )

        self.assertEqual(
            response.status_code,
            302,
        )

        solicitacao = (
            SolicitacaoCadastro.objects.get(
                nome="Empresa Solicitada"
            )
        )

        self.assertEqual(
            solicitacao.status,
            SolicitacaoCadastro.STATUS_PENDENTE,
        )

        self.assertEqual(
            solicitacao.plano_id,
            self.plano.pk,
        )

    def test_solicitacao_profissional_exige_especialidade(self):
        response = self.client.post(
            reverse(
                "cadastros:anuncie"
            ),
            {
                "plano": self.plano.pk,
                "tipo": SolicitacaoCadastro.TIPO_PROFISSIONAL,
                "nome": "Profissional Sem Especialidade",
                "responsavel": "",
                "cidade": self.cidade.pk,
                "categoria": self.categoria.pk,
                "especialidade": "",
                "descricao": "",
                "endereco": "",
                "bairro": "",
                "telefone": "",
                "whatsapp": "37966666666",
                "email": "",
                "instagram": "",
                "site": "",
                "horario": "",
            },
        )

        self.assertEqual(
            response.status_code,
            200,
        )

        self.assertFalse(
            SolicitacaoCadastro.objects.filter(
                nome="Profissional Sem Especialidade"
            ).exists()
        )

    def test_staff_aprova_solicitacao_empresa(self):
        solicitacao = (
            SolicitacaoCadastro.objects.create(
                plano=self.plano,
                tipo=SolicitacaoCadastro.TIPO_EMPRESA,
                nome="Empresa Aprovacao",
                responsavel="Responsavel",
                cidade=self.cidade,
                categoria=self.categoria,
                descricao=(
                    "Descricao da empresa para aprovacao."
                ),
                whatsapp="37955555555",
                status=SolicitacaoCadastro.STATUS_PENDENTE,
            )
        )

        self.client.force_login(
            self.staff
        )

        response = self.client.post(
            reverse(
                "administracao:aprovar_solicitacao",
                kwargs={
                    "solicitacao_id": solicitacao.pk,
                },
            )
        )

        self.assertEqual(
            response.status_code,
            302,
        )

        solicitacao.refresh_from_db()

        self.assertEqual(
            solicitacao.status,
            SolicitacaoCadastro.STATUS_APROVADO,
        )

        self.assertTrue(
            Empresa.objects.filter(
                nome_fantasia="Empresa Aprovacao",
                cidade=self.cidade,
            ).exists()
        )

    def test_staff_recusa_solicitacao(self):
        solicitacao = (
            SolicitacaoCadastro.objects.create(
                plano=self.plano,
                tipo=SolicitacaoCadastro.TIPO_PROFISSIONAL,
                nome="Profissional Recusa",
                cidade=self.cidade,
                categoria=self.categoria,
                especialidade="Teste",
                whatsapp="37944444444",
                status=SolicitacaoCadastro.STATUS_PENDENTE,
            )
        )

        self.client.force_login(
            self.staff
        )

        response = self.client.post(
            reverse(
                "administracao:recusar_solicitacao",
                kwargs={
                    "solicitacao_id": solicitacao.pk,
                },
            )
        )

        self.assertEqual(
            response.status_code,
            302,
        )

        solicitacao.refresh_from_db()

        self.assertEqual(
            solicitacao.status,
            SolicitacaoCadastro.STATUS_RECUSADO,
        )

        self.assertFalse(
            Profissional.objects.filter(
                nome="Profissional Recusa",
                cidade=self.cidade,
            ).exists()
        )

    def test_nao_staff_nao_aprova_solicitacao(self):
        solicitacao = (
            SolicitacaoCadastro.objects.create(
                plano=self.plano,
                tipo=SolicitacaoCadastro.TIPO_EMPRESA,
                nome="Empresa Protegida",
                cidade=self.cidade,
                categoria=self.categoria,
                whatsapp="37933333333",
                status=SolicitacaoCadastro.STATUS_PENDENTE,
            )
        )

        self.client.force_login(
            self.cliente
        )

        response = self.client.post(
            reverse(
                "administracao:aprovar_solicitacao",
                kwargs={
                    "solicitacao_id": solicitacao.pk,
                },
            )
        )

        self.assertEqual(
            response.status_code,
            302,
        )

        solicitacao.refresh_from_db()

        self.assertEqual(
            solicitacao.status,
            SolicitacaoCadastro.STATUS_PENDENTE,
        )

        self.assertFalse(
            Empresa.objects.filter(
                nome_fantasia="Empresa Protegida"
            ).exists()
        )

    def test_avaliacao_aprovada_aparece_no_perfil_empresa(self):
        Avaliacao.objects.create(
            empresa=self.empresa,
            nome="Avaliador Aprovado",
            nota=5,
            comentario="Comentario aprovado Enterprise.",
            aprovado=True,
        )

        response = self.client.get(
            reverse(
                "core:empresa_detalhe",
                kwargs={
                    "cidade_slug": self.cidade.slug,
                    "empresa_slug": self.empresa.slug,
                },
            )
        )

        self.assertContains(
            response,
            "Comentario aprovado Enterprise.",
        )

    def test_avaliacao_pendente_nao_aparece_no_perfil_empresa(self):
        Avaliacao.objects.create(
            empresa=self.empresa,
            nome="Avaliador Pendente",
            nota=4,
            comentario="Comentario ainda pendente.",
            aprovado=False,
        )

        response = self.client.get(
            reverse(
                "core:empresa_detalhe",
                kwargs={
                    "cidade_slug": self.cidade.slug,
                    "empresa_slug": self.empresa.slug,
                },
            )
        )

        self.assertNotContains(
            response,
            "Comentario ainda pendente.",
        )