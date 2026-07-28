from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from apps.cadastros.models import SolicitacaoCadastro
from apps.categorias.models import Categoria
from apps.cidades.models import Cidade


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

    def test_usuario_comum_nao_aprova_solicitacao(self):
        usuario = get_user_model().objects.create_user(
            username="cliente-aprovacao",
            password="senha-segura-123",
        )
        cidade = Cidade.objects.create(nome="Teste", estado="MG")
        categoria = Categoria.objects.create(nome="Serviços")
        solicitacao = SolicitacaoCadastro.objects.create(
            tipo=SolicitacaoCadastro.TIPO_EMPRESA,
            nome="Empresa pendente",
            cidade=cidade,
            categoria=categoria,
            whatsapp="37999999999",
            status=SolicitacaoCadastro.STATUS_PENDENTE,
        )
        self.client.force_login(usuario)

        resposta = self.client.post(
            reverse(
                "administracao:aprovar_solicitacao",
                args=[solicitacao.pk],
            )
        )

        self.assertEqual(resposta.status_code, 302)
        self.assertIn("/admin/login/", resposta.url)
        solicitacao.refresh_from_db()
        self.assertEqual(
            solicitacao.status,
            SolicitacaoCadastro.STATUS_PENDENTE,
        )
