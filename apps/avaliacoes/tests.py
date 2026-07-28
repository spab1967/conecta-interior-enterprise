from django.core.cache import cache
from django.test import TestCase
from django.urls import reverse

from apps.categorias.models import Categoria
from apps.cidades.models import Cidade
from apps.empresas.models import Empresa

from .models import Avaliacao


class AvaliacaoValidationTests(TestCase):
    def setUp(self):
        cache.clear()
        cidade = Cidade.objects.create(nome="Teste", estado="MG")
        categoria = Categoria.objects.create(nome="Serviços")
        self.empresa = Empresa.objects.create(
            cidade=cidade,
            categoria=categoria,
            nome_fantasia="Empresa avaliada",
        )
        self.url = reverse(
            "avaliacoes:avaliar_empresa",
            args=[cidade.slug, self.empresa.slug],
        )

    def test_rejeita_nome_acima_do_limite(self):
        resposta = self.client.post(
            self.url,
            {
                "nome": "A" * 121,
                "nota": "5",
                "comentario": "Atendimento excelente.",
            },
        )

        self.assertContains(resposta, "no máximo 120 caracteres")
        self.assertFalse(Avaliacao.objects.exists())

    def test_rejeita_comentario_excessivo(self):
        resposta = self.client.post(
            self.url,
            {
                "nome": "Cliente",
                "nota": "5",
                "comentario": "A" * 2001,
            },
        )

        self.assertContains(resposta, "no máximo 2.000 caracteres")
        self.assertFalse(Avaliacao.objects.exists())

    def test_limita_envios_repetidos_de_avaliacao(self):
        dados = {
            "nome": "Cliente",
            "nota": "5",
            "comentario": "Atendimento excelente.",
        }

        for _ in range(5):
            resposta = self.client.post(
                self.url,
                dados,
                REMOTE_ADDR="203.0.113.10",
            )
            self.assertEqual(resposta.status_code, 302)

        resposta = self.client.post(
            self.url,
            dados,
            REMOTE_ADDR="203.0.113.10",
        )

        self.assertEqual(resposta.status_code, 403)
        self.assertEqual(Avaliacao.objects.count(), 5)
