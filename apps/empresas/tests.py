from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from apps.categorias.models import Categoria
from apps.cidades.models import Cidade

from .models import Empresa


class EmpresaClienteAccessTests(TestCase):
    def setUp(self):
        User = get_user_model()
        self.usuario = User.objects.create_user(
            username="cliente",
            password="senha-segura-123",
        )
        self.outro_usuario = User.objects.create_user(
            username="outro-cliente",
            password="senha-segura-123",
        )
        self.cidade = Cidade.objects.create(nome="Teste", estado="MG")
        self.categoria = Categoria.objects.create(nome="Serviços")
        self.empresa = Empresa.objects.create(
            usuario=self.usuario,
            cidade=self.cidade,
            categoria=self.categoria,
            nome_fantasia="Empresa do cliente",
        )
        self.empresa_alheia = Empresa.objects.create(
            usuario=self.outro_usuario,
            cidade=self.cidade,
            categoria=self.categoria,
            nome_fantasia="Empresa de outro cliente",
        )
        self.client.force_login(self.usuario)

    def test_lista_exibe_apenas_empresas_do_usuario(self):
        resposta = self.client.get(reverse("empresas:listar"))

        self.assertContains(resposta, self.empresa.nome_fantasia)
        self.assertNotContains(resposta, self.empresa_alheia.nome_fantasia)

    def test_cliente_nao_visualiza_empresa_de_outro_usuario(self):
        resposta = self.client.get(
            reverse("empresas:visualizar", args=[self.empresa_alheia.pk])
        )

        self.assertEqual(resposta.status_code, 404)

    def test_cliente_nao_edita_empresa_de_outro_usuario(self):
        resposta = self.client.post(
            reverse("empresas:editar", args=[self.empresa_alheia.pk]),
            {"nome_fantasia": "Nome alterado"},
        )

        self.assertEqual(resposta.status_code, 404)
        self.empresa_alheia.refresh_from_db()
        self.assertEqual(
            self.empresa_alheia.nome_fantasia,
            "Empresa de outro cliente",
        )
