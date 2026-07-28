from decimal import Decimal
from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import (
    TestCase,
    override_settings,
)
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

    def test_cadastro_publico_cria_acesso_e_empresa_automaticamente(self):
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
                "email": "empresa.solicitada@example.com",
                "instagram": "",
                "site": "",
                "horario": "",
                "senha": "SenhaForte@123",
                "confirmar_senha": "SenhaForte@123",
            },
        )

        self.assertEqual(
            response.status_code,
            302,
        )

        self.assertEqual(
            response.url,
            reverse("core:minha_conta"),
        )

        solicitacao = (
            SolicitacaoCadastro.objects.get(
                nome="Empresa Solicitada"
            )
        )

        self.assertEqual(
            solicitacao.status,
            SolicitacaoCadastro.STATUS_APROVADO,
        )

        self.assertEqual(
            solicitacao.plano_id,
            self.plano.pk,
        )

        usuario = get_user_model().objects.get(
            username="empresa.solicitada@example.com"
        )

        self.assertTrue(
            usuario.is_active
        )

        self.assertTrue(
            usuario.check_password("SenhaForte@123")
        )

        empresa = Empresa.objects.get(
            nome_fantasia="Empresa Solicitada"
        )

        self.assertEqual(
            empresa.usuario_id,
            usuario.pk,
        )

        self.assertTrue(
            empresa.ativa
        )

        response = self.client.get(
            reverse("core:minha_conta")
        )

        self.assertEqual(
            response.status_code,
            200,
        )

        self.assertContains(
            response,
            "Empresa Solicitada",
        )

        response = self.client.get(
            reverse(
                "core:selecionar_plano",
                kwargs={
                    "plano_id": self.plano.pk,
                },
            )
        )

        self.assertEqual(
            response.status_code,
            200,
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
                "email": "profissional.sem@example.com",
                "instagram": "",
                "site": "",
                "horario": "",
                "senha": "SenhaForte@123",
                "confirmar_senha": "SenhaForte@123",
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

        self.assertFalse(
            get_user_model().objects.filter(
                username="profissional.sem@example.com"
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

    def test_aprovacao_vincula_e_ativa_usuario_da_solicitacao(self):
        User = get_user_model()

        usuario = User.objects.create_user(
            username="cliente.aprovacao@example.com",
            email="cliente.aprovacao@example.com",
            password="SenhaForte@123",
            is_active=False,
        )

        solicitacao = SolicitacaoCadastro.objects.create(
            plano=self.plano,
            tipo=SolicitacaoCadastro.TIPO_EMPRESA,
            nome="Empresa Com Acesso",
            responsavel="Cliente Aprovacao",
            cidade=self.cidade,
            categoria=self.categoria,
            descricao="Descricao valida da empresa com acesso.",
            whatsapp="37911112222",
            email="cliente.aprovacao@example.com",
            status=SolicitacaoCadastro.STATUS_PENDENTE,
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

        usuario.refresh_from_db()

        empresa = Empresa.objects.get(
            nome_fantasia="Empresa Com Acesso",
        )

        self.assertEqual(
            empresa.usuario_id,
            usuario.pk,
        )

        self.assertTrue(
            usuario.is_active
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

    def test_plano_gratis_ativa_sem_cobranca_para_empresa(self):
        plano_gratis = Plano.objects.create(
            nome="Plano Gratis",
            descricao="Plano gratuito para testes",
            preco_mensal=Decimal("0.00"),
            ativo=True,
            ordem=1,
        )

        assinatura_anterior = Assinatura.objects.create(
            empresa=self.empresa,
            profissional=None,
            plano=self.plano,
            status=Assinatura.STATUS_ATIVA,
        )

        pedido_antigo = PedidoFinanceiro.objects.create(
            empresa=self.empresa,
            profissional=None,
            plano=plano_gratis,
            valor=Decimal("0.00"),
            status=PedidoFinanceiro.STATUS_PENDENTE,
        )

        self.client.force_login(
            self.cliente
        )

        response = self.client.post(
            reverse(
                "core:alterar_plano_empresa",
                kwargs={
                    "plano_id": plano_gratis.pk,
                    "empresa_id": self.empresa.pk,
                },
            )
        )

        self.assertRedirects(
            response,
            reverse("core:minha_conta"),
        )

        assinatura_anterior.refresh_from_db()
        pedido_antigo.refresh_from_db()

        self.assertEqual(
            assinatura_anterior.status,
            Assinatura.STATUS_CANCELADA,
        )

        self.assertEqual(
            pedido_antigo.status,
            PedidoFinanceiro.STATUS_CANCELADO,
        )

        self.assertFalse(
            PedidoFinanceiro.objects.filter(
                empresa=self.empresa,
                status=PedidoFinanceiro.STATUS_PENDENTE,
            ).exists()
        )

        assinatura_atual = Assinatura.objects.get(
            empresa=self.empresa,
            profissional__isnull=True,
            status=Assinatura.STATUS_ATIVA,
        )

        self.assertEqual(
            assinatura_atual.plano_id,
            plano_gratis.pk,
        )

        response = self.client.get(
            reverse("core:minha_conta")
        )

        self.assertContains(
            response,
            "Mudar de plano",
        )

        self.assertNotContains(
            response,
            "Cobrança pendente",
        )

    def test_plano_gratis_ativa_sem_cobranca_para_profissional(self):
        plano_gratis = Plano.objects.create(
            nome="Plano Gratis Profissional",
            descricao="Plano gratuito para profissional",
            preco_mensal=Decimal("0.00"),
            ativo=True,
            ordem=2,
        )

        self.client.force_login(
            self.cliente
        )

        response = self.client.post(
            reverse(
                "core:alterar_plano_profissional",
                kwargs={
                    "plano_id": plano_gratis.pk,
                    "profissional_id": self.profissional.pk,
                },
            )
        )

        self.assertRedirects(
            response,
            reverse("core:minha_conta"),
        )

        self.assertFalse(
            PedidoFinanceiro.objects.filter(
                profissional=self.profissional,
                status=PedidoFinanceiro.STATUS_PENDENTE,
            ).exists()
        )

        assinatura_atual = Assinatura.objects.get(
            profissional=self.profissional,
            empresa__isnull=True,
            status=Assinatura.STATUS_ATIVA,
        )

        self.assertEqual(
            assinatura_atual.plano_id,
            plano_gratis.pk,
        )

    def test_nova_escolha_cancela_cobranca_pendente_anterior(self):
        plano_anterior = Plano.objects.create(
            nome="Plano Pendente Anterior",
            preco_mensal=Decimal("19.90"),
            ativo=True,
            ordem=20,
        )

        pedido_anterior = PedidoFinanceiro.objects.create(
            empresa=self.empresa,
            profissional=None,
            plano=plano_anterior,
            valor=plano_anterior.preco_mensal,
            status=PedidoFinanceiro.STATUS_PENDENTE,
        )

        self.client.force_login(
            self.cliente
        )

        response = self.client.post(
            reverse(
                "core:alterar_plano_empresa",
                kwargs={
                    "plano_id": self.plano.pk,
                    "empresa_id": self.empresa.pk,
                },
            )
        )

        self.assertEqual(
            response.status_code,
            302,
        )

        pedido_anterior.refresh_from_db()

        self.assertEqual(
            pedido_anterior.status,
            PedidoFinanceiro.STATUS_CANCELADO,
        )

        pendentes = PedidoFinanceiro.objects.filter(
            empresa=self.empresa,
            profissional__isnull=True,
            status=PedidoFinanceiro.STATUS_PENDENTE,
        )

        self.assertEqual(
            pendentes.count(),
            1,
        )

        self.assertEqual(
            pendentes.get().plano_id,
            self.plano.pk,
        )

    def test_pagamento_aprovado_remove_todos_os_planos_antigos(self):
        plano_antigo = Plano.objects.create(
            nome="Plano Antigo",
            preco_mensal=Decimal("10.00"),
            ativo=True,
            ordem=30,
        )

        primeira = Assinatura.objects.create(
            empresa=self.empresa,
            profissional=None,
            plano=plano_antigo,
            status=Assinatura.STATUS_ATIVA,
        )

        segunda = Assinatura.objects.create(
            empresa=self.empresa,
            profissional=None,
            plano=plano_antigo,
            status=Assinatura.STATUS_ATIVA,
        )

        pedido = self._pedido_empresa()

        pagamento = Pagamento.objects.create(
            pedido=pedido,
            tipo=Pagamento.TIPO_PIX,
            status=Pagamento.STATUS_PENDENTE,
            valor=pedido.valor,
        )

        aprovar_pagamento(pagamento)

        primeira.refresh_from_db()
        segunda.refresh_from_db()

        self.assertEqual(
            primeira.status,
            Assinatura.STATUS_CANCELADA,
        )

        self.assertEqual(
            segunda.status,
            Assinatura.STATUS_CANCELADA,
        )

        ativas = Assinatura.objects.filter(
            empresa=self.empresa,
            profissional__isnull=True,
            status=Assinatura.STATUS_ATIVA,
        )

        self.assertEqual(
            ativas.count(),
            1,
        )

        self.assertEqual(
            ativas.get().plano_id,
            self.plano.pk,
        )

    @override_settings(
        MERCADO_PAGO_ACCESS_TOKEN="TEST-ACCESS-TOKEN",
        MERCADO_PAGO_WEBHOOK_SECRET="TEST-WEBHOOK-SECRET",
        MERCADO_PAGO_ATIVO=True,
    )
    @patch(
        "apps.financeiro.views."
        "criar_ou_obter_pix_mercado_pago"
    )
    def test_pagamento_exibe_qr_code_mercado_pago(
        self,
        criar_pix,
    ):
        pedido = self._pedido_empresa()

        criar_pix.return_value = {
            "id": 123456789,
            "status": "pending",
            "status_detail": "pending_waiting_transfer",
            "point_of_interaction": {
                "transaction_data": {
                    "qr_code": "PIX-COPIA-E-COLA-TESTE",
                    "qr_code_base64": "aW1hZ2VtLXRlc3Rl",
                    "ticket_url": "https://www.mercadopago.com.br/teste",
                }
            },
        }

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

        self.assertContains(
            response,
            "PIX-COPIA-E-COLA-TESTE",
        )

        self.assertContains(
            response,
            "QR Code PIX do Mercado Pago",
        )

        self.assertNotContains(
            response,
            "Favorecido:",
        )

    @override_settings(
        MERCADO_PAGO_ACCESS_TOKEN="TEST-ACCESS-TOKEN",
        MERCADO_PAGO_WEBHOOK_SECRET="TEST-WEBHOOK-SECRET",
        MERCADO_PAGO_ATIVO=True,
    )
    @patch(
        "apps.financeiro.views."
        "consultar_pagamento_mercado_pago"
    )
    @patch(
        "apps.financeiro.views."
        "WebhookSignatureValidator.validate"
    )
    def test_webhook_aprovado_ativa_plano(
        self,
        validar_assinatura,
        consultar_pagamento,
    ):
        pedido = self._pedido_empresa()

        pagamento = Pagamento.objects.create(
            pedido=pedido,
            tipo=Pagamento.TIPO_PIX,
            status=Pagamento.STATUS_PENDENTE,
            valor=pedido.valor,
            codigo_transacao="123456789",
        )

        consultar_pagamento.return_value = {
            "id": 123456789,
            "status": "approved",
            "external_reference": str(
                pedido.pk
            ),
            "transaction_amount": str(
                pedido.valor
            ),
            "payment_method_id": "pix",
        }

        response = self.client.post(
            (
                reverse(
                    "financeiro:webhook_mercado_pago"
                )
                + "?type=payment&data.id=123456789"
            ),
            data=(
                '{"type":"payment",'
                '"data":{"id":"123456789"}}'
            ),
            content_type="application/json",
            HTTP_X_SIGNATURE="ts=1,v1=teste",
            HTTP_X_REQUEST_ID="request-teste",
        )

        self.assertEqual(
            response.status_code,
            200,
        )

        validar_assinatura.assert_called_once()
        pagamento.refresh_from_db()
        pedido.refresh_from_db()

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

    @override_settings(
        MERCADO_PAGO_ACCESS_TOKEN="TEST-ACCESS-TOKEN",
        MERCADO_PAGO_WEBHOOK_SECRET="TEST-WEBHOOK-SECRET",
        MERCADO_PAGO_ATIVO=True,
    )
    @patch(
        "apps.financeiro.views."
        "consultar_pagamento_mercado_pago"
    )
    @patch(
        "apps.financeiro.views."
        "WebhookSignatureValidator.validate"
    )
    def test_webhook_rejeita_valor_divergente(
        self,
        validar_assinatura,
        consultar_pagamento,
    ):
        pedido = self._pedido_empresa()

        pagamento = Pagamento.objects.create(
            pedido=pedido,
            tipo=Pagamento.TIPO_PIX,
            status=Pagamento.STATUS_PENDENTE,
            valor=pedido.valor,
            codigo_transacao="987654321",
        )

        consultar_pagamento.return_value = {
            "id": 987654321,
            "status": "approved",
            "external_reference": str(
                pedido.pk
            ),
            "transaction_amount": "1.00",
            "payment_method_id": "pix",
        }

        response = self.client.post(
            (
                reverse(
                    "financeiro:webhook_mercado_pago"
                )
                + "?type=payment&data.id=987654321"
            ),
            data=(
                '{"type":"payment",'
                '"data":{"id":"987654321"}}'
            ),
            content_type="application/json",
            HTTP_X_SIGNATURE="ts=1,v1=teste",
            HTTP_X_REQUEST_ID="request-teste",
        )

        self.assertEqual(
            response.status_code,
            400,
        )

        pagamento.refresh_from_db()
        pedido.refresh_from_db()

        self.assertEqual(
            pagamento.status,
            Pagamento.STATUS_PENDENTE,
        )

        self.assertEqual(
            pedido.status,
            PedidoFinanceiro.STATUS_PENDENTE,
        )

