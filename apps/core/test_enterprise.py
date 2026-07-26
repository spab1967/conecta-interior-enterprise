from django.conf import settings
from django.test import SimpleTestCase
from django.urls import resolve, reverse

from apps.servicos.models import Servico


class EnterpriseArchitectureTests(SimpleTestCase):
    """Testes de integridade estrutural da Conecta Interior Enterprise 1.0."""

    def test_home_route(self):
        self.assertEqual(reverse("core:home"), "/")

    def test_planos_route(self):
        self.assertEqual(reverse("core:planos"), "/planos/")

    def test_login_route(self):
        self.assertEqual(reverse("core:login"), "/entrar/")

    def test_minha_conta_route(self):
        self.assertEqual(reverse("core:minha_conta"), "/minha-conta/")

    def test_administracao_dashboard_route(self):
        self.assertEqual(
            reverse("administracao:dashboard"),
            "/administracao/",
        )

    def test_administracao_empresas_route(self):
        self.assertEqual(
            reverse("administracao:empresas"),
            "/administracao/empresas/",
        )

    def test_administracao_profissionais_route(self):
        self.assertEqual(
            reverse("administracao:profissionais"),
            "/administracao/profissionais/",
        )

    def test_administracao_servicos_route(self):
        self.assertEqual(
            reverse("administracao:servicos"),
            "/administracao/servicos/",
        )

    def test_administracao_solicitacoes_route(self):
        self.assertEqual(
            reverse("administracao:solicitacoes"),
            "/administracao/solicitacoes/",
        )

    def test_administracao_assinaturas_route(self):
        self.assertEqual(
            reverse("administracao:assinaturas"),
            "/administracao/assinaturas/",
        )

    def test_administracao_financeiro_route(self):
        self.assertEqual(
            reverse("administracao:financeiro"),
            "/administracao/financeiro/",
        )

    def test_administracao_avaliacoes_route(self):
        self.assertEqual(
            reverse("administracao:avaliacoes"),
            "/administracao/avaliacoes/",
        )

    def test_administracao_metricas_route(self):
        self.assertEqual(
            reverse("administracao:metricas"),
            "/administracao/metricas/",
        )

    def test_administracao_configuracoes_route(self):
        self.assertEqual(
            reverse("administracao:configuracoes"),
            "/administracao/configuracoes/",
        )

    def test_favoritos_route(self):
        self.assertEqual(
            reverse("favoritos:meus_favoritos"),
            "/favoritos/",
        )

    def test_cadastros_route(self):
        self.assertEqual(
            reverse("cadastros:anuncie"),
            "/cadastros/",
        )

    def test_avaliacoes_sucesso_route(self):
        self.assertEqual(
            reverse("avaliacoes:sucesso"),
            "/avaliacoes/sucesso/",
        )

    def test_financeiro_historico_route(self):
        self.assertEqual(
            reverse("financeiro:historico"),
            "/financeiro/historico/",
        )

    def test_servicos_empresa_route(self):
        self.assertEqual(
            reverse("servicos:gerenciar_empresa", kwargs={"empresa_id": 1}),
            "/servicos/empresa/1/",
        )

    def test_servicos_profissional_route(self):
        self.assertEqual(
            reverse(
                "servicos:gerenciar_profissional",
                kwargs={"profissional_id": 1},
            ),
            "/servicos/profissional/1/",
        )

    def test_servico_exige_um_titular(self):
        nomes = {
            constraint.name
            for constraint in Servico._meta.constraints
        }
        self.assertIn("servico_um_titular", nomes)

    def test_servico_tem_relacao_empresa(self):
        campo = Servico._meta.get_field("empresa")
        self.assertTrue(campo.null)
        self.assertTrue(campo.blank)

    def test_servico_tem_relacao_profissional(self):
        campo = Servico._meta.get_field("profissional")
        self.assertTrue(campo.null)
        self.assertTrue(campo.blank)

    def test_timezone_oficial(self):
        self.assertEqual(settings.TIME_ZONE, "America/Sao_Paulo")

    def test_language_oficial(self):
        self.assertEqual(settings.LANGUAGE_CODE, "pt-br")

    def test_login_redirect(self):
        self.assertEqual(settings.LOGIN_REDIRECT_URL, "core:minha_conta")

    def test_logout_redirect(self):
        self.assertEqual(settings.LOGOUT_REDIRECT_URL, "core:home")

    def test_servicos_url_resolve(self):
        match = resolve("/servicos/empresa/1/")
        self.assertEqual(match.url_name, "gerenciar_empresa")

    def test_admin_servicos_url_resolve(self):
        match = resolve("/administracao/servicos/")
        self.assertEqual(match.url_name, "servicos")
