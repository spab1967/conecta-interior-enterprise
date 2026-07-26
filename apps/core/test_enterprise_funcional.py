from datetime import timedelta
from decimal import Decimal

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from apps.avaliacoes.models import Avaliacao
from apps.cadastros.models import SolicitacaoCadastro
from apps.categorias.models import Categoria
from apps.cidades.models import Cidade
from apps.empresas.models import Empresa
from apps.favoritos.models import Favorito
from apps.profissionais.models import Profissional
from apps.servicos.models import Servico


class EnterpriseFunctionalFlowTests(TestCase):

    @classmethod
    def setUpTestData(cls):
        User = get_user_model()

        cls.usuario = User.objects.create_user(
            username="cliente_enterprise_teste",
            password="Teste@123",
        )

        cls.outro_usuario = User.objects.create_user(
            username="outro_cliente_enterprise",
            password="Teste@123",
        )

        cls.cidade = Cidade.objects.create(
            nome="Cidade Teste Enterprise",
            estado="MG",
            slug="cidade-teste-enterprise",
        )

        cls.categoria = Categoria.objects.create(
            nome="Categoria Teste Enterprise",
            slug="categoria-teste-enterprise",
        )

        cls.empresa = Empresa.objects.create(
            usuario=cls.usuario,
            cidade=cls.cidade,
            categoria=cls.categoria,
            nome_fantasia="Empresa Funcional Enterprise",
            descricao="Empresa criada exclusivamente para testes.",
            whatsapp="37999999999",
            ativa=True,
        )

        cls.profissional = Profissional.objects.create(
            usuario=cls.usuario,
            cidade=cls.cidade,
            categoria=cls.categoria,
            nome="Profissional Funcional Enterprise",
            especialidade="Serviço de teste",
            whatsapp="37988888888",
            ativo=True,
        )

    def test_home_responde_200(self):
        response = self.client.get(reverse("core:home"))
        self.assertEqual(response.status_code, 200)

    def test_planos_responde_200(self):
        response = self.client.get(reverse("core:planos"))
        self.assertEqual(response.status_code, 200)

    def test_login_responde_200(self):
        response = self.client.get(reverse("core:login"))
        self.assertEqual(response.status_code, 200)

    def test_minha_conta_exige_login(self):
        response = self.client.get(reverse("core:minha_conta"))
        self.assertEqual(response.status_code, 302)

    def test_minha_conta_autenticada_responde_200(self):
        self.client.force_login(self.usuario)
        response = self.client.get(reverse("core:minha_conta"))
        self.assertEqual(response.status_code, 200)

    def test_perfil_publico_empresa_responde_200(self):
        response = self.client.get(
            reverse(
                "core:empresa_detalhe",
                kwargs={
                    "cidade_slug": self.cidade.slug,
                    "empresa_slug": self.empresa.slug,
                },
            )
        )
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, self.empresa.nome_fantasia)

    def test_perfil_publico_profissional_responde_200(self):
        response = self.client.get(
            reverse(
                "core:profissional_detalhe",
                kwargs={
                    "cidade_slug": self.cidade.slug,
                    "profissional_slug": self.profissional.slug,
                },
            )
        )
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, self.profissional.nome)

    def test_servico_empresa_pode_ser_criado_pelo_dono(self):
        self.client.force_login(self.usuario)
        response = self.client.post(
            reverse(
                "servicos:gerenciar_empresa",
                kwargs={"empresa_id": self.empresa.pk},
            ),
            {
                "nome": "Instalação Enterprise",
                "valor": "150.00",
                "ativo": "on",
            },
        )
        self.assertEqual(response.status_code, 302)
        servico = Servico.objects.get(
            empresa=self.empresa,
            nome="Instalação Enterprise",
        )
        self.assertEqual(servico.cidade, self.cidade)
        self.assertIsNone(servico.profissional)
        self.assertEqual(servico.valor, Decimal("150.00"))

    def test_servico_profissional_pode_ser_criado_pelo_dono(self):
        self.client.force_login(self.usuario)
        response = self.client.post(
            reverse(
                "servicos:gerenciar_profissional",
                kwargs={"profissional_id": self.profissional.pk},
            ),
            {
                "nome": "Atendimento Enterprise",
                "valor": "",
                "ativo": "on",
            },
        )
        self.assertEqual(response.status_code, 302)
        servico = Servico.objects.get(
            profissional=self.profissional,
            nome="Atendimento Enterprise",
        )
        self.assertEqual(servico.cidade, self.cidade)
        self.assertIsNone(servico.empresa)
        self.assertIsNone(servico.valor)

    def test_outro_usuario_nao_gerencia_servicos_da_empresa(self):
        self.client.force_login(self.outro_usuario)
        response = self.client.get(
            reverse(
                "servicos:gerenciar_empresa",
                kwargs={"empresa_id": self.empresa.pk},
            )
        )
        self.assertEqual(response.status_code, 404)

    def test_outro_usuario_nao_gerencia_servicos_do_profissional(self):
        self.client.force_login(self.outro_usuario)
        response = self.client.get(
            reverse(
                "servicos:gerenciar_profissional",
                kwargs={"profissional_id": self.profissional.pk},
            )
        )
        self.assertEqual(response.status_code, 404)

    def test_servico_ativo_aparece_no_perfil_empresa(self):
        Servico.objects.create(
            cidade=self.cidade,
            empresa=self.empresa,
            nome="Serviço Público Enterprise",
            valor=Decimal("99.90"),
            ativo=True,
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
        self.assertContains(response, "Serviço Público Enterprise")

    def test_servico_inativo_nao_aparece_no_perfil_empresa(self):
        Servico.objects.create(
            cidade=self.cidade,
            empresa=self.empresa,
            nome="Serviço Oculto Enterprise",
            ativo=False,
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
        self.assertNotContains(response, "Serviço Oculto Enterprise")

    def test_avaliacao_empresa_e_criada_pendente(self):
        response = self.client.post(
            reverse(
                "avaliacoes:avaliar_empresa",
                kwargs={
                    "cidade_slug": self.cidade.slug,
                    "empresa_slug": self.empresa.slug,
                },
            ),
            {
                "nome": "Cliente Teste",
                "nota": "5",
                "comentario": "Excelente atendimento.",
            },
        )
        self.assertEqual(response.status_code, 302)
        avaliacao = Avaliacao.objects.get(
            empresa=self.empresa,
            nome="Cliente Teste",
        )
        self.assertEqual(avaliacao.nota, 5)
        self.assertFalse(avaliacao.aprovado)

    def test_avaliacao_profissional_e_criada_pendente(self):
        response = self.client.post(
            reverse(
                "avaliacoes:avaliar_profissional",
                kwargs={
                    "cidade_slug": self.cidade.slug,
                    "profissional_slug": self.profissional.slug,
                },
            ),
            {
                "nome": "Cliente Profissional",
                "nota": "4",
                "comentario": "Muito bom.",
            },
        )
        self.assertEqual(response.status_code, 302)
        avaliacao = Avaliacao.objects.get(
            profissional=self.profissional,
            nome="Cliente Profissional",
        )
        self.assertEqual(avaliacao.nota, 4)
        self.assertFalse(avaliacao.aprovado)

    def test_favoritar_empresa_cria_registro(self):
        response = self.client.post(
            reverse(
                "favoritos:alternar_empresa",
                kwargs={
                    "cidade_slug": self.cidade.slug,
                    "empresa_slug": self.empresa.slug,
                },
            )
        )
        self.assertEqual(response.status_code, 302)
        self.assertEqual(
            Favorito.objects.filter(empresa=self.empresa).count(),
            1,
        )

    def test_favoritar_empresa_novamente_remove_registro(self):
        url = reverse(
            "favoritos:alternar_empresa",
            kwargs={
                "cidade_slug": self.cidade.slug,
                "empresa_slug": self.empresa.slug,
            },
        )
        self.client.post(url)
        self.client.post(url)
        self.assertFalse(
            Favorito.objects.filter(empresa=self.empresa).exists()
        )

    def test_favoritar_profissional_cria_registro(self):
        response = self.client.post(
            reverse(
                "favoritos:alternar_profissional",
                kwargs={
                    "cidade_slug": self.cidade.slug,
                    "profissional_slug": self.profissional.slug,
                },
            )
        )
        self.assertEqual(response.status_code, 302)
        self.assertEqual(
            Favorito.objects.filter(
                profissional=self.profissional
            ).count(),
            1,
        )

    def test_whatsapp_empresa_gera_link(self):
        self.assertIn(
            "https://wa.me/55",
            self.empresa.whatsapp_link,
        )
        self.assertIn(
            "Conecta",
            self.empresa.whatsapp_link,
        )

    def test_whatsapp_profissional_gera_link(self):
        self.assertIn(
            "https://wa.me/55",
            self.profissional.whatsapp_link,
        )
        self.assertIn(
            "Conecta",
            self.profissional.whatsapp_link,
        )
