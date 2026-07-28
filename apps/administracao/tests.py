from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse


class SolicitacoesAccessTests(TestCase):
    def test_usuario_comum_nao_acessa_solicitacoes_administrativas(self):
        usuario = get_user_model().objects.create_user(
            username="cliente",
            password="senha-segura-123",
        )
        self.client.force_login(usuario)

        resposta = self.client.get(reverse("administracao:solicitacoes"))

        self.assertEqual(resposta.status_code, 302)
        self.assertIn("/admin/login/", resposta.url)
