from decimal import Decimal
from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.contrib.auth.models import AnonymousUser
from django.db import OperationalError
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from apps.categorias.models import Categoria
from apps.cidades.models import Cidade
from apps.empresas.models import Empresa
from apps.financeiro.models import Pagamento, PedidoFinanceiro
from apps.planos.models import Assinatura, Plano
from apps.profissionais.models import Profissional
from apps.servicos.models import Servico


class EnterpriseCriticalFlowTests(TestCase):

    @classmethod
    def setUpTestData(cls):
        User = get_user_model()

        cls.usuario = User.objects.create_user(
            username="cliente_critico",
            password="Teste@123",
        )
        cls.invasor = User.objects.create_user(
            username="cliente_invasor",
            password="Teste@123",
        )
        cls.staff = User.objects.create_user(
            username="admin_critico",
            password="Teste@123",
            is_staff=True,
        )

        cls.cidade = Cidade.objects.create(
            nome="Cidade Critica",
            estado="MG",
            slug="cidade-critica",
        )
        cls.categoria = Categoria.objects.create(
            nome="Categoria Critica",
            slug="categoria-critica",
        )

        cls.empresa = Empresa.objects.create(
            usuario=cls.usuario,
            cidade=cls.cidade,
            categoria=cls.categoria,
            nome_fantasia="Empresa Critica",
            ativa=True,
        )
        cls.profissional = Profissional.objects.create(
            usuario=cls.usuario,
            cidade=cls.cidade,
            categoria=cls.categoria,
            nome="Profissional Critico",
            ativo=True,
        )

    def test_admin_enterprise_exige_staff(self):
        self.client.force_login(self.usuario)
        response = self.client.get(reverse("administracao:dashboard"))
        self.assertIn(response.status_code, (302, 403))

    def test_health_confirma_aplicacao_e_banco(self):
        response = self.client.get(reverse("core:health"))

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), {"status": "ok"})
        self.assertEqual(response["Cache-Control"], "no-store")

    @patch(
        "apps.core.views.connection.ensure_connection",
        side_effect=OperationalError,
    )
    def test_health_retorna_503_quando_banco_falha(
        self,
        ensure_connection,
    ):
        response = self.client.get(reverse("core:health"))

        self.assertEqual(response.status_code, 503)
        self.assertEqual(
            response.json(),
            {"status": "indisponivel"},
        )

    def test_admin_enterprise_staff_acessa(self):
        self.client.force_login(self.staff)
        response = self.client.get(reverse("administracao:dashboard"))
        self.assertEqual(response.status_code, 200)

    def test_servico_edicao_exige_dono(self):
        servico = Servico.objects.create(
            cidade=self.cidade,
            empresa=self.empresa,
            nome="Servico Protegido",
            valor=Decimal("50.00"),
            ativo=True,
        )
        self.client.force_login(self.invasor)
        response = self.client.get(
            reverse("servicos:editar", kwargs={"servico_id": servico.pk})
        )
        self.assertEqual(response.status_code, 404)

    def test_servico_exclusao_exige_dono(self):
        servico = Servico.objects.create(
            cidade=self.cidade,
            profissional=self.profissional,
            nome="Servico Nao Excluir",
            ativo=True,
        )
        self.client.force_login(self.invasor)
        response = self.client.post(
            reverse("servicos:excluir", kwargs={"servico_id": servico.pk})
        )
        self.assertEqual(response.status_code, 404)
        self.assertTrue(Servico.objects.filter(pk=servico.pk).exists())

    def test_servico_dono_pode_alternar_status(self):
        servico = Servico.objects.create(
            cidade=self.cidade,
            empresa=self.empresa,
            nome="Servico Alternavel",
            ativo=True,
        )
        self.client.force_login(self.usuario)
        response = self.client.post(
            reverse(
                "servicos:alternar_ativo",
                kwargs={"servico_id": servico.pk},
            )
        )
        self.assertEqual(response.status_code, 302)
        servico.refresh_from_db()
        self.assertFalse(servico.ativo)

    def test_servico_dono_pode_excluir(self):
        servico = Servico.objects.create(
            cidade=self.cidade,
            empresa=self.empresa,
            nome="Servico Excluivel",
            ativo=True,
        )
        self.client.force_login(self.usuario)
        response = self.client.post(
            reverse("servicos:excluir", kwargs={"servico_id": servico.pk})
        )
        self.assertEqual(response.status_code, 302)
        self.assertFalse(Servico.objects.filter(pk=servico.pk).exists())

    def test_empresa_inativa_nao_tem_perfil_publico(self):
        empresa = Empresa.objects.create(
            usuario=self.usuario,
            cidade=self.cidade,
            categoria=self.categoria,
            nome_fantasia="Empresa Inativa",
            ativa=False,
        )
        response = self.client.get(
            reverse(
                "core:empresa_detalhe",
                kwargs={
                    "cidade_slug": self.cidade.slug,
                    "empresa_slug": empresa.slug,
                },
            )
        )
        self.assertEqual(response.status_code, 404)

    def test_profissional_inativo_nao_tem_perfil_publico(self):
        profissional = Profissional.objects.create(
            usuario=self.usuario,
            cidade=self.cidade,
            categoria=self.categoria,
            nome="Profissional Inativo",
            ativo=False,
        )
        response = self.client.get(
            reverse(
                "core:profissional_detalhe",
                kwargs={
                    "cidade_slug": self.cidade.slug,
                    "profissional_slug": profissional.slug,
                },
            )
        )
        self.assertEqual(response.status_code, 404)

    def test_whatsapp_sem_numero_retorna_vazio_empresa(self):
        self.empresa.whatsapp = ""
        self.assertEqual(self.empresa.whatsapp_link, "")

    def test_whatsapp_sem_numero_retorna_vazio_profissional(self):
        self.profissional.whatsapp = ""
        self.assertEqual(self.profissional.whatsapp_link, "")

    def test_slug_empresa_e_gerado(self):
        self.assertTrue(self.empresa.slug)
        self.assertIn("empresa-critica", self.empresa.slug)

    def test_slug_profissional_e_gerado(self):
        self.assertTrue(self.profissional.slug)
        self.assertIn("profissional-critico", self.profissional.slug)

    def test_slug_empresa_mesmo_nome_na_mesma_cidade_e_unico(self):
        segunda = Empresa.objects.create(
            cidade=self.cidade,
            categoria=self.categoria,
            nome_fantasia=self.empresa.nome_fantasia,
            ativa=True,
        )
        self.assertNotEqual(self.empresa.slug, segunda.slug)

    def test_slug_profissional_mesmo_nome_na_mesma_cidade_e_unico(self):
        segundo = Profissional.objects.create(
            cidade=self.cidade,
            categoria=self.categoria,
            nome=self.profissional.nome,
            ativo=True,
        )
        self.assertNotEqual(self.profissional.slug, segundo.slug)

    def test_servico_empresa_forca_cidade_do_titular(self):
        outra = Cidade.objects.create(
            nome="Cidade Outra",
            estado="MG",
            slug="cidade-outra",
        )
        servico = Servico.objects.create(
            cidade=outra,
            empresa=self.empresa,
            nome="Cidade Corrigida Empresa",
        )
        self.assertEqual(servico.cidade_id, self.empresa.cidade_id)

    def test_servico_profissional_forca_cidade_do_titular(self):
        outra = Cidade.objects.create(
            nome="Cidade Terceira",
            estado="MG",
            slug="cidade-terceira",
        )
        servico = Servico.objects.create(
            cidade=outra,
            profissional=self.profissional,
            nome="Cidade Corrigida Profissional",
        )
        self.assertEqual(servico.cidade_id, self.profissional.cidade_id)

    def test_servico_sem_titular_falha_validacao(self):
        servico = Servico(
            cidade=self.cidade,
            nome="Sem Titular",
        )
        with self.assertRaises(Exception):
            servico.full_clean()

    def test_servico_com_dois_titulares_falha_validacao(self):
        servico = Servico(
            cidade=self.cidade,
            empresa=self.empresa,
            profissional=self.profissional,
            nome="Dois Titulares",
        )
        with self.assertRaises(Exception):
            servico.full_clean()
