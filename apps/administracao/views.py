from django.shortcuts import get_object_or_404, redirect
from apps.servicos.models import Servico
from django.contrib import messages
from django.contrib.auth.forms import SetPasswordForm
from django.db import transaction
from django.views.decorators.http import require_POST
from django.conf import settings
import django
import platform
from apps.metricas.models import EventoContato
from django.db.models import Q
from decimal import Decimal

from django.contrib.admin.views.decorators import staff_member_required
from django.core.paginator import Paginator
from django.db.models import Avg, Q, Sum
from django.shortcuts import render
from django.utils import timezone

from apps.avaliacoes.models import Avaliacao
from apps.cadastros.models import SolicitacaoCadastro
from apps.categorias.models import Categoria
from apps.cidades.models import Cidade
from apps.empresas.models import Empresa
from apps.financeiro.models import Pagamento, PedidoFinanceiro
from apps.planos.models import Assinatura
from apps.profissionais.models import Profissional


def _contar_assinaturas_ativas():
    """
    Conta assinaturas ativas sem alterar o modelo existente.
    """

    nomes_campos = {
        campo.name
        for campo in Assinatura._meta.get_fields()
    }

    if "ativa" in nomes_campos:
        return Assinatura.objects.filter(
            ativa=True,
        ).count()

    if "ativo" in nomes_campos:
        return Assinatura.objects.filter(
            ativo=True,
        ).count()

    if "status" in nomes_campos:
        valores_ativos = [
            "ativa",
            "ativo",
            "active",
        ]

        return Assinatura.objects.filter(
            status__in=valores_ativos,
        ).count()

    if "data_fim" in nomes_campos:
        return Assinatura.objects.filter(
            data_fim__gte=timezone.localdate(),
        ).count()

    return Assinatura.objects.count()


def _contexto_painel():
    pagamentos_aprovados = Pagamento.objects.filter(
        status=Pagamento.STATUS_APROVADO,
    )

    avaliacoes_aprovadas = Avaliacao.objects.filter(
        aprovado=True,
    )

    return {
        "total_empresas": Empresa.objects.count(),
        "total_profissionais": Profissional.objects.count(),
        "total_categorias": Categoria.objects.count(),
        "total_cidades": Cidade.objects.count(),
        "total_pedidos": PedidoFinanceiro.objects.count(),
        "total_pagamentos": Pagamento.objects.count(),
        "pagamentos_aprovados": pagamentos_aprovados.count(),
        "total_avaliacoes": avaliacoes_aprovadas.count(),
        "total_assinaturas": Assinatura.objects.count(),
        "assinaturas_ativas": _contar_assinaturas_ativas(),

        "ultimas_empresas": (
            Empresa.objects
            .select_related(
                "cidade",
                "categoria",
            )
            .order_by("-criada_em")[:5]
        ),

        "ultimos_profissionais": (
            Profissional.objects
            .select_related(
                "cidade",
                "categoria",
                "empresa",
            )
            .order_by("-criado_em")[:5]
        ),
    }


@staff_member_required
def dashboard(request):
    agora = timezone.localtime()

    inicio_mes = agora.replace(
        day=1,
        hour=0,
        minute=0,
        second=0,
        microsecond=0,
    )

    pagamentos_aprovados = Pagamento.objects.filter(
        status=Pagamento.STATUS_APROVADO,
    )

    receita_total = (
        pagamentos_aprovados.aggregate(
            total=Sum("valor"),
        )["total"]
        or Decimal("0.00")
    )

    receita_mes = (
        pagamentos_aprovados.filter(
            pago_em__gte=inicio_mes,
        ).aggregate(
            total=Sum("valor"),
        )["total"]
        or Decimal("0.00")
    )

    ticket_medio = (
        pagamentos_aprovados.aggregate(
            media=Avg("valor"),
        )["media"]
        or Decimal("0.00")
    )

    avaliacoes_aprovadas = Avaliacao.objects.filter(
        aprovado=True,
    )

    media_avaliacoes = (
        avaliacoes_aprovadas.aggregate(
            media=Avg("nota"),
        )["media"]
        or 0
    )

    eventos_contato = EventoContato.objects.all()

    total_contatos = eventos_contato.count()

    contatos_mes = eventos_contato.filter(
        criado_em__gte=inicio_mes,
    ).count()

    contatos_whatsapp = eventos_contato.filter(
        tipo="whatsapp",
    ).count()

    contatos_telefone = eventos_contato.filter(
        tipo="telefone",
    ).count()

    contatos_email = eventos_contato.filter(
        tipo="email",
    ).count()

    novas_empresas_mes = Empresa.objects.filter(
        criada_em__gte=inicio_mes,
    ).count()

    novos_profissionais_mes = Profissional.objects.filter(
        criado_em__gte=inicio_mes,
    ).count()

    cadastros_mes = (
        novas_empresas_mes
        + novos_profissionais_mes
    )

    contexto = {
        "total_empresas": Empresa.objects.count(),
        "empresas_ativas": Empresa.objects.filter(
            ativa=True,
        ).count(),

        "total_profissionais": Profissional.objects.count(),
        "profissionais_ativos": Profissional.objects.filter(
            ativo=True,
        ).count(),

        "assinaturas_ativas": _contar_assinaturas_ativas(),

        "total_avaliacoes": avaliacoes_aprovadas.count(),
        "media_avaliacoes": media_avaliacoes,

        "receita_total": receita_total,
        "receita_mes": receita_mes,
        "ticket_medio": ticket_medio,
        "total_pagamentos": pagamentos_aprovados.count(),

        "total_cidades": Cidade.objects.count(),
        "total_categorias": Categoria.objects.count(),
        "total_pedidos": PedidoFinanceiro.objects.count(),

        "total_contatos": total_contatos,
        "contatos_mes": contatos_mes,
        "contatos_whatsapp": contatos_whatsapp,
        "contatos_telefone": contatos_telefone,
        "contatos_email": contatos_email,

        "novas_empresas_mes": novas_empresas_mes,
        "novos_profissionais_mes": novos_profissionais_mes,
        "cadastros_mes": cadastros_mes,

        "ultimas_empresas": (
            Empresa.objects
            .select_related(
                "cidade",
                "categoria",
            )
            .order_by("-criada_em")[:5]
        ),

        "ultimos_profissionais": (
            Profissional.objects
            .select_related(
                "cidade",
                "categoria",
                "empresa",
            )
            .order_by("-criado_em")[:5]
        ),
    }

    return render(
        request,
        "administracao/dashboard.html",
        contexto,
    )


@staff_member_required
def painel(request):
    contexto = _contexto_painel()
    contexto["titulo_pagina"] = "Painel Administrativo"

    return render(
        request,
        "administracao/painel.html",
        contexto,
    )


@staff_member_required
def empresas(request):
    pesquisa = request.GET.get(
        "q",
        "",
    ).strip()

    empresas_cadastradas = (
        Empresa.objects
        .select_related(
            "cidade",
            "categoria",
            "usuario",
        )
        .order_by(
            "-destaque",
            "nome_fantasia",
        )
    )

    if pesquisa:
        empresas_cadastradas = empresas_cadastradas.filter(
            Q(nome_fantasia__icontains=pesquisa)
            | Q(cidade__nome__icontains=pesquisa)
            | Q(categoria__nome__icontains=pesquisa)
        )

    total_empresas = empresas_cadastradas.count()

    empresas_ativas = empresas_cadastradas.filter(
        ativa=True,
    ).count()

    paginator = Paginator(
        empresas_cadastradas,
        20,
    )

    page_obj = paginator.get_page(
        request.GET.get("page")
    )

    return render(
        request,
        "administracao/empresas.html",
        {
            "empresas": empresas_cadastradas,
            "page_obj": page_obj,
            "pesquisa": pesquisa,
            "total_empresas": total_empresas,
            "empresas_ativas": empresas_ativas,
        },
    )


@staff_member_required
def profissionais(request):
    pesquisa = request.GET.get("q", "").strip()

    profissionais_cadastrados = (
        Profissional.objects
        .select_related("cidade", "categoria", "empresa", "usuario")
        .order_by("-destaque", "nome")
    )

    if pesquisa:
        profissionais_cadastrados = profissionais_cadastrados.filter(
            Q(nome__icontains=pesquisa)
            | Q(especialidade__icontains=pesquisa)
            | Q(cidade__nome__icontains=pesquisa)
            | Q(categoria__nome__icontains=pesquisa)
            | Q(empresa__nome_fantasia__icontains=pesquisa)
        )

    total_profissionais = profissionais_cadastrados.count()
    profissionais_ativos = profissionais_cadastrados.filter(ativo=True).count()

    paginator = Paginator(profissionais_cadastrados, 20)
    page_obj = paginator.get_page(request.GET.get("page"))

    return render(
        request,
        "administracao/profissionais.html",
        {
            "page_obj": page_obj,
            "pesquisa": pesquisa,
            "total_profissionais": total_profissionais,
            "profissionais_ativos": profissionais_ativos,
        },
    )

@staff_member_required
def assinaturas(request):
    pesquisa = request.GET.get("q", "").strip()

    assinaturas_cadastradas = (
        Assinatura.objects
        .select_related("plano", "empresa", "profissional")
        .order_by("-inicio", "-criada_em")
    )

    if pesquisa:
        assinaturas_cadastradas = assinaturas_cadastradas.filter(
            Q(plano__nome__icontains=pesquisa)
            | Q(status__icontains=pesquisa)
            | Q(empresa__nome_fantasia__icontains=pesquisa)
            | Q(profissional__nome__icontains=pesquisa)
        )

    total_assinaturas = assinaturas_cadastradas.count()
    assinaturas_ativas = assinaturas_cadastradas.filter(
        status=Assinatura.STATUS_ATIVA,
    ).count()

    paginator = Paginator(assinaturas_cadastradas, 20)
    page_obj = paginator.get_page(request.GET.get("page"))

    return render(
        request,
        "administracao/assinaturas.html",
        {
            "page_obj": page_obj,
            "pesquisa": pesquisa,
            "total_assinaturas": total_assinaturas,
            "assinaturas_ativas": assinaturas_ativas,
        },
    )

@staff_member_required
def financeiro(request):
    pesquisa = request.GET.get("q", "").strip()

    pedidos_qs = (
        PedidoFinanceiro.objects
        .select_related("empresa", "profissional", "plano", "assinatura")
        .order_by("-criado_em")
    )

    if pesquisa:
        pedidos_qs = pedidos_qs.filter(
            Q(empresa__nome_fantasia__icontains=pesquisa)
            | Q(profissional__nome__icontains=pesquisa)
            | Q(plano__nome__icontains=pesquisa)
            | Q(status__icontains=pesquisa)
        )

    pagamentos_qs = (
        Pagamento.objects
        .select_related("pedido", "pedido__empresa", "pedido__profissional")
        .order_by("-criado_em")
    )

    hoje = timezone.localdate()

    total_pedidos = PedidoFinanceiro.objects.count()
    pedidos_pendentes = PedidoFinanceiro.objects.filter(
        status=PedidoFinanceiro.STATUS_PENDENTE
    ).count()
    total_pagamentos = Pagamento.objects.count()
    pagamentos_aprovados = Pagamento.objects.filter(
        status=Pagamento.STATUS_APROVADO
    ).count()

    receita_total = (
        Pagamento.objects
        .filter(status=Pagamento.STATUS_APROVADO)
        .aggregate(total=Sum("valor"))["total"]
        or Decimal("0.00")
    )

    receita_mes = (
        Pagamento.objects
        .filter(
            status=Pagamento.STATUS_APROVADO,
            pago_em__year=hoje.year,
            pago_em__month=hoje.month,
        )
        .aggregate(total=Sum("valor"))["total"]
        or Decimal("0.00")
    )

    return render(
        request,
        "administracao/financeiro.html",
        {
            "pedidos": pedidos_qs[:20],
            "pagamentos": pagamentos_qs[:20],
            "pesquisa": pesquisa,
            "total_pedidos": total_pedidos,
            "pedidos_pendentes": pedidos_pendentes,
            "total_pagamentos": total_pagamentos,
            "pagamentos_aprovados": pagamentos_aprovados,
            "receita_total": receita_total,
            "receita_mes": receita_mes,
        },
    )

@staff_member_required
def pagamentos(request):
    pagamentos_cadastrados = (
        Pagamento.objects
        .select_related(
            "pedido",
            "pedido__empresa",
            "pedido__profissional",
            "pedido__plano",
        )
        .order_by("-criado_em")
    )

    return render(
        request,
        "administracao/painel.html",
        {
            "titulo_pagina": "Pagamentos",
            "registros": pagamentos_cadastrados,
            "total_registros": pagamentos_cadastrados.count(),
        },
    )


@staff_member_required
def avaliacoes(request):
    pesquisa = request.GET.get("q", "").strip()

    avaliacoes_qs = (
        Avaliacao.objects
        .select_related("empresa", "profissional")
        .order_by("-criado_em")
    )

    if pesquisa:
        avaliacoes_qs = avaliacoes_qs.filter(
            Q(nome__icontains=pesquisa)
            | Q(comentario__icontains=pesquisa)
            | Q(empresa__nome_fantasia__icontains=pesquisa)
            | Q(profissional__nome__icontains=pesquisa)
        )

    total_avaliacoes = avaliacoes_qs.count()
    avaliacoes_aprovadas = avaliacoes_qs.filter(aprovado=True).count()
    avaliacoes_pendentes = avaliacoes_qs.filter(aprovado=False).count()

    media_avaliacoes = (
        avaliacoes_qs
        .filter(aprovado=True)
        .aggregate(media=Avg("nota"))["media"]
        or 0
    )

    paginator = Paginator(avaliacoes_qs, 20)
    page_obj = paginator.get_page(request.GET.get("page"))

    return render(
        request,
        "administracao/avaliacoes.html",
        {
            "page_obj": page_obj,
            "pesquisa": pesquisa,
            "total_avaliacoes": total_avaliacoes,
            "avaliacoes_aprovadas": avaliacoes_aprovadas,
            "avaliacoes_pendentes": avaliacoes_pendentes,
            "media_avaliacoes": media_avaliacoes,
        },
    )

@staff_member_required
def metricas(request):
    busca = request.GET.get("q", "").strip()
    tipo = request.GET.get("tipo", "").strip()
    eventos = EventoContato.objects.select_related("empresa","empresa__cidade","profissional","profissional__cidade").all()
    total_eventos = eventos.count()
    eventos_hoje = eventos.filter(criado_em__date=timezone.localdate()).count()
    contatos_whatsapp = eventos.filter(tipo=EventoContato.TIPO_WHATSAPP).count()
    contatos_telefone = eventos.filter(tipo=EventoContato.TIPO_TELEFONE).count()

    if busca:
        eventos = eventos.filter(
            Q(empresa__nome_fantasia__icontains=busca) |
            Q(profissional__nome__icontains=busca) |
            Q(empresa__cidade__nome__icontains=busca) |
            Q(profissional__cidade__nome__icontains=busca)
        )

    tipos_validos = {valor for valor, rotulo in EventoContato.TIPOS}
    if tipo in tipos_validos:
        eventos = eventos.filter(tipo=tipo)

    distribuicao = []
    for valor, rotulo in EventoContato.TIPOS:
        distribuicao.append({"valor":valor,"rotulo":rotulo,"quantidade":EventoContato.objects.filter(tipo=valor).count()})

    pagina = Paginator(eventos, 20).get_page(request.GET.get("page"))
    return render(request, "administracao/metricas.html", {
        "total_eventos":total_eventos,
        "eventos_hoje":eventos_hoje,
        "contatos_whatsapp":contatos_whatsapp,
        "contatos_telefone":contatos_telefone,
        "distribuicao":distribuicao,
        "pagina":pagina,
        "busca":busca,
        "tipo_selecionado":tipo,
        "tipos":EventoContato.TIPOS,
    })

def solicitacoes(request):
    pesquisa = request.GET.get("q", "").strip()

    solicitacoes_cadastradas = (
        SolicitacaoCadastro.objects
        .select_related("cidade", "categoria", "plano")
        .order_by("-criado_em")
    )

    if pesquisa:
        solicitacoes_cadastradas = solicitacoes_cadastradas.filter(
            Q(nome__icontains=pesquisa)
            | Q(responsavel__icontains=pesquisa)
            | Q(especialidade__icontains=pesquisa)
            | Q(cidade__nome__icontains=pesquisa)
            | Q(categoria__nome__icontains=pesquisa)
        )

    total_solicitacoes = solicitacoes_cadastradas.count()
    total_pendentes = solicitacoes_cadastradas.filter(
        status=SolicitacaoCadastro.STATUS_PENDENTE,
    ).count()

    paginator = Paginator(solicitacoes_cadastradas, 20)
    page_obj = paginator.get_page(request.GET.get("page"))

    return render(
        request,
        "administracao/solicitacoes.html",
        {
            "page_obj": page_obj,
            "pesquisa": pesquisa,
            "total_solicitacoes": total_solicitacoes,
            "total_pendentes": total_pendentes,
        },
    )

@staff_member_required
def cidades(request):
    cidades_cadastradas = Cidade.objects.all()

    return render(
        request,
        "administracao/painel.html",
        {
            "titulo_pagina": "Cidades",
            "registros": cidades_cadastradas,
            "total_registros": cidades_cadastradas.count(),
        },
    )


@staff_member_required
def categorias(request):
    categorias_cadastradas = Categoria.objects.all()

    return render(
        request,
        "administracao/painel.html",
        {
            "titulo_pagina": "Categorias",
            "registros": categorias_cadastradas,
            "total_registros": categorias_cadastradas.count(),
        },
    )


@staff_member_required
def configuracoes(request):
    banco_engine = (
        settings.DATABASES
        .get("default", {})
        .get("ENGINE", "")
        .rsplit(".", 1)[-1]
        or "Não identificado"
    )

    nomes_banco = {
        "sqlite3": "SQLite",
        "postgresql": "PostgreSQL",
        "mysql": "MySQL",
        "oracle": "Oracle",
    }

    return render(
        request,
        "administracao/configuracoes.html",
        {
            "django_version": django.get_version(),
            "python_version": platform.python_version(),
            "banco_engine": nomes_banco.get(
                banco_engine,
                banco_engine,
            ),
            "debug_status": "Ativo" if settings.DEBUG else "Desativado",
        },
    )

@require_POST
@transaction.atomic
def aprovar_solicitacao(request, solicitacao_id):

    if not request.user.is_authenticated or not request.user.is_staff:
        messages.error(request, "Acesso administrativo necessario.")
        return redirect("administracao:solicitacoes")

    solicitacao = get_object_or_404(
        SolicitacaoCadastro.objects.select_for_update().select_related(
            "cidade",
            "categoria",
            "plano",
        ),
        pk=solicitacao_id,
    )

    if solicitacao.status != SolicitacaoCadastro.STATUS_PENDENTE:
        messages.warning(request, "Esta solicitacao ja foi processada.")
        return redirect("administracao:solicitacoes")

    if solicitacao.tipo == SolicitacaoCadastro.TIPO_EMPRESA:

        if not solicitacao.categoria:
            messages.error(request, "A solicitacao de empresa nao possui categoria.")
            return redirect("administracao:solicitacoes")

        Empresa.objects.create(
            cidade=solicitacao.cidade,
            categoria=solicitacao.categoria,
            nome_fantasia=solicitacao.nome,
            descricao=solicitacao.descricao,
            endereco=solicitacao.endereco,
            bairro=solicitacao.bairro,
            telefone=solicitacao.telefone,
            whatsapp=solicitacao.whatsapp,
            email=solicitacao.email,
            instagram=solicitacao.instagram,
            site=solicitacao.site,
            horario=solicitacao.horario,
            ativa=True,
        )

    elif solicitacao.tipo == SolicitacaoCadastro.TIPO_PROFISSIONAL:

        Profissional.objects.create(
            cidade=solicitacao.cidade,
            categoria=solicitacao.categoria,
            nome=solicitacao.nome,
            especialidade=solicitacao.especialidade,
            descricao=solicitacao.descricao,
            endereco=solicitacao.endereco,
            bairro=solicitacao.bairro,
            telefone=solicitacao.telefone,
            whatsapp=solicitacao.whatsapp,
            email=solicitacao.email,
            instagram=solicitacao.instagram,
            site=solicitacao.site,
            horario=solicitacao.horario,
            ativo=True,
        )

    else:
        messages.error(request, "Tipo de solicitacao invalido.")
        return redirect("administracao:solicitacoes")

    solicitacao.status = SolicitacaoCadastro.STATUS_APROVADO

    plano_texto = ""
    if solicitacao.plano:
        plano_texto = " Plano solicitado preservado: " + solicitacao.plano.nome + "."

    observacao_anterior = (solicitacao.observacao_admin or "").strip()
    complemento = "Cadastro criado pela aprovacao administrativa." + plano_texto

    if observacao_anterior:
        solicitacao.observacao_admin = observacao_anterior + chr(10) + complemento
    else:
        solicitacao.observacao_admin = complemento

    solicitacao.save(
        update_fields=[
            "status",
            "observacao_admin",
            "atualizado_em",
        ]
    )

    messages.success(request, "Solicitacao aprovada e cadastro criado.")
    return redirect("administracao:solicitacoes")


@require_POST
@transaction.atomic
def recusar_solicitacao(request, solicitacao_id):

    if not request.user.is_authenticated or not request.user.is_staff:
        messages.error(request, "Acesso administrativo necessario.")
        return redirect("administracao:solicitacoes")

    solicitacao = get_object_or_404(
        SolicitacaoCadastro.objects.select_for_update(),
        pk=solicitacao_id,
    )

    if solicitacao.status != SolicitacaoCadastro.STATUS_PENDENTE:
        messages.warning(request, "Esta solicitacao ja foi processada.")
        return redirect("administracao:solicitacoes")

    solicitacao.status = SolicitacaoCadastro.STATUS_RECUSADO

    observacao_anterior = (solicitacao.observacao_admin or "").strip()
    complemento = "Solicitacao recusada pela administracao."

    if observacao_anterior:
        solicitacao.observacao_admin = observacao_anterior + chr(10) + complemento
    else:
        solicitacao.observacao_admin = complemento

    solicitacao.save(
        update_fields=[
            "status",
            "observacao_admin",
            "atualizado_em",
        ]
    )

    messages.success(request, "Solicitacao recusada.")
    return redirect("administracao:solicitacoes")

@staff_member_required
def servicos(request):

    pesquisa = request.GET.get("q", "").strip()

    servicos_qs = (
        Servico.objects
        .select_related("cidade", "empresa", "profissional")
        .order_by("-ativo", "nome")
    )

    if pesquisa:
        servicos_qs = servicos_qs.filter(
            Q(nome__icontains=pesquisa)
            | Q(empresa__nome_fantasia__icontains=pesquisa)
            | Q(profissional__nome__icontains=pesquisa)
            | Q(cidade__nome__icontains=pesquisa)
        )

    total_servicos = servicos_qs.count()
    servicos_ativos = servicos_qs.filter(ativo=True).count()

    paginator = Paginator(servicos_qs, 20)
    page_obj = paginator.get_page(request.GET.get("page"))

    return render(
        request,
        "administracao/servicos.html",
        {
            "page_obj": page_obj,
            "pesquisa": pesquisa,
            "total_servicos": total_servicos,
            "servicos_ativos": servicos_ativos,
        },
    )



@staff_member_required
def definir_senha_empresa(request, empresa_id):
    empresa = get_object_or_404(Empresa.objects.select_related("usuario"), pk=empresa_id)
    if not empresa.usuario:
        messages.error(request, "Esta empresa não possui usuário responsável vinculado.")
        return redirect("administracao:empresas")
    form = SetPasswordForm(empresa.usuario, request.POST or None)
    if request.method == "POST" and form.is_valid():
        form.save()
        messages.success(request, f"Senha do usuário {empresa.usuario.username} definida com sucesso.")
        return redirect("administracao:empresas")
    return render(request, "administracao/definir_senha.html", {
        "form": form, "usuario_alvo": empresa.usuario,
        "cadastro": empresa.nome_fantasia, "tipo": "Empresa",
        "voltar_url": "administracao:empresas",
    })


@staff_member_required
def definir_senha_profissional(request, profissional_id):
    profissional = get_object_or_404(Profissional.objects.select_related("usuario"), pk=profissional_id)
    if not profissional.usuario:
        messages.error(request, "Este profissional não possui usuário responsável vinculado.")
        return redirect("administracao:profissionais")
    form = SetPasswordForm(profissional.usuario, request.POST or None)
    if request.method == "POST" and form.is_valid():
        form.save()
        messages.success(request, f"Senha do usuário {profissional.usuario.username} definida com sucesso.")
        return redirect("administracao:profissionais")
    return render(request, "administracao/definir_senha.html", {
        "form": form, "usuario_alvo": profissional.usuario,
        "cadastro": profissional.nome, "tipo": "Profissional",
        "voltar_url": "administracao:profissionais",
    })
