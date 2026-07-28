from django.test import TestCase
from django.urls import reverse


class PlanoInicialValidationTests(TestCase):
    def test_plano_invalido_na_url_e_ignorado(self):
        resposta = self.client.get(
            reverse("cadastros:anuncie"),
            {"plano": "valor-invalido"},
        )

        self.assertEqual(resposta.status_code, 200)
        self.assertIsNone(resposta.context["plano_selecionado"])
