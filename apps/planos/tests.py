from datetime import timedelta
from decimal import Decimal

from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from apps.categorias.models import Categoria
from apps.cidades.models import Cidade
from apps.empresas.models import Empresa
from apps.profissionais.models import Profissional

from .models import Assinatura, Plano
from .services import (
    STATUS_ATRASO, STATUS_LIBERADA, STATUS_REGULAR, STATUS_SUSPENSA,
    situacao_financeira,
)


class RegraInadimplenciaTests(TestCase):
    def setUp(self):
        self.hoje = timezone.localdate()
        self.cidade = Cidade.objects.create(nome="Abaeté", estado="MG")
        self.categoria = Categoria.objects.create(nome="Serviços")
        self.empresa = Empresa.objects.create(
            nome_fantasia="Empresa teste", cidade=self.cidade,
            categoria=self.categoria,
        )
        self.profissional = Profissional.objects.create(
            nome="Profissional teste", cidade=self.cidade,
            categoria=self.categoria,
        )
        self.pago = Plano.objects.create(
            nome="Destaque", preco_mensal=Decimal("49.90")
        )
        self.gratuito = Plano.objects.create(
            nome="Gratuito", preco_mensal=Decimal("0.00")
        )

    def assinatura(self, titular, plano, vencimento):
        kwargs = {"empresa": titular} if isinstance(titular, Empresa) else {"profissional": titular}
        return Assinatura.objects.create(
            plano=plano, inicio=self.hoje - timedelta(days=30),
            vencimento=vencimento, status=Assinatura.STATUS_ATIVA, **kwargs,
        )

    def test_plano_gratuito_nao_publica_pagina(self):
        self.assinatura(self.empresa, self.gratuito, None)
        situacao = situacao_financeira(empresa=self.empresa)
        self.assertEqual(situacao.codigo, STATUS_REGULAR)
        self.assertFalse(situacao.pagina_publica)

    def test_sem_assinatura_nao_publica_pagina(self):
        self.assertFalse(
            situacao_financeira(profissional=self.profissional).pagina_publica
        )

    def test_gratuito_nao_aparece_na_home_e_nao_tem_acesso_direto(self):
        self.assinatura(self.empresa, self.gratuito, None)
        resposta_home = self.client.get(reverse("core:home"))
        self.assertNotContains(resposta_home, self.empresa.nome_fantasia)
        resposta_perfil = self.client.get(reverse(
            "core:empresa_detalhe",
            args=[self.cidade.slug, self.empresa.slug],
        ))
        self.assertEqual(resposta_perfil.status_code, 404)

    def test_sete_dias_de_tolerancia(self):
        self.assinatura(self.empresa, self.pago, self.hoje - timedelta(days=7))
        self.assertEqual(situacao_financeira(empresa=self.empresa).codigo, STATUS_ATRASO)

    def test_suspende_no_oitavo_dia_empresa_e_profissional(self):
        vencimento = self.hoje - timedelta(days=8)
        self.assinatura(self.empresa, self.pago, vencimento)
        self.assinatura(self.profissional, self.pago, vencimento)
        self.assertEqual(situacao_financeira(empresa=self.empresa).codigo, STATUS_SUSPENSA)
        self.assertEqual(situacao_financeira(profissional=self.profissional).codigo, STATUS_SUSPENSA)

    def test_liberacao_manual_reativa_pagina(self):
        self.assinatura(self.empresa, self.pago, self.hoje - timedelta(days=8))
        self.empresa.liberacao_financeira_ativa = True
        self.empresa.liberacao_financeira_ate = self.hoje + timedelta(days=3)
        self.empresa.save()
        situacao = situacao_financeira(empresa=self.empresa)
        self.assertEqual(situacao.codigo, STATUS_LIBERADA)
        self.assertTrue(situacao.pagina_publica)

    def test_suspensa_sai_da_home_e_exibe_aviso_no_acesso_direto(self):
        self.assinatura(
            self.empresa, self.pago, self.hoje - timedelta(days=8)
        )
        resposta_home = self.client.get(reverse("core:home"))
        self.assertNotContains(resposta_home, self.empresa.nome_fantasia)

        resposta_perfil = self.client.get(reverse(
            "core:empresa_detalhe",
            args=[self.cidade.slug, self.empresa.slug],
        ))
        self.assertEqual(resposta_perfil.status_code, 200)
        self.assertContains(resposta_perfil, "Página temporariamente indisponível")

    def test_durante_tolerancia_pagina_continua_publica(self):
        self.assinatura(
            self.profissional, self.pago, self.hoje - timedelta(days=7)
        )
        resposta = self.client.get(reverse(
            "core:profissional_detalhe",
            args=[self.cidade.slug, self.profissional.slug],
        ))
        self.assertEqual(resposta.status_code, 200)
        self.assertNotContains(resposta, "Página temporariamente indisponível")

# Create your tests here.
