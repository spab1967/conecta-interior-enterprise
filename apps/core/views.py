from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.http import Http404
from django.db.models import (
    Avg,
    Case,
    IntegerField,
    Q,
    Value,
    When,
)
from django.shortcuts import (
    get_object_or_404,
    redirect,
    render,
)
from django.utils import timezone

from apps.cidades.models import Cidade
from apps.categorias.models import Categoria
from apps.empresas.forms import EmpresaClienteForm
from apps.empresas.models import Empresa
from apps.financeiro.models import PedidoFinanceiro
from apps.planos.models import Assinatura, Plano
from apps.planos.services import (
    assinatura_vigente,
    plano_vigente,
)
from apps.planos.vigencia import calcular_vencimento_plano
from apps.profissionais.forms import ProfissionalClienteForm
from apps.profissionais.models import Profissional


def _ids_por_prioridade_comercial(
    tipo_titular,
):
    """
    Retorna os IDs dos titulares que possuem
    assinatura Premium ou Destaque vigente.

    A assinatura precisa estar:
    - ativa;
    - iniciada;
    - n├úo vencida;
    - vinculada a um plano ativo.
    """

    hoje = timezone.localdate()

    filtro_vigencia = (
        Q(vencimento__isnull=True)
        | Q(vencimento__gte=hoje)
    )

    assinaturas = (
        Assinatura.objects
        .filter(
            status=Assinatura.STATUS_ATIVA,
            inicio__lte=hoje,
            plano__ativo=True,
        )
        .filter(
            filtro_vigencia
        )
    )

    if tipo_titular == "empresa":

        assinaturas = assinaturas.filter(
            empresa__isnull=False,
            profissional__isnull=True,
        )

        premium = list(
            assinaturas.filter(
                plano__nome__iexact="Premium"
            ).values_list(
                "empresa_id",
                flat=True,
            )
        )

        destaque = list(
            assinaturas.filter(
                plano__nome__iexact="Destaque"
            ).values_list(
                "empresa_id",
                flat=True,
            )
        )

    else:

        assinaturas = assinaturas.filter(
            profissional__isnull=False,
            empresa__isnull=True,
        )

        premium = list(
            assinaturas.filter(
                plano__nome__iexact="Premium"
            ).values_list(
                "profissional_id",
                flat=True,
            )
        )

        destaque = list(
            assinaturas.filter(
                plano__nome__iexact="Destaque"
            ).values_list(
                "profissional_id",
                flat=True,
            )
        )

    return (
        premium,
        destaque,
    )


def _ordenar_empresas(empresas):

    premium_ids, destaque_ids = (
        _ids_por_prioridade_comercial(
            "empresa"
        )
    )

    return (
        empresas
        .annotate(
            prioridade_comercial=Case(
                When(
                    pk__in=premium_ids,
                    then=Value(3),
                ),
                When(
                    pk__in=destaque_ids,
                    then=Value(2),
                ),
                default=Value(1),
                output_field=IntegerField(),
            )
        )
        .order_by(
            "-prioridade_comercial",
            "-destaque",
            "nome_fantasia",
        )
    )


def _ordenar_profissionais(
    profissionais,
):

    premium_ids, destaque_ids = (
        _ids_por_prioridade_comercial(
            "profissional"
        )
    )

    return (
        profissionais
        .annotate(
            prioridade_comercial=Case(
                When(
                    pk__in=premium_ids,
                    then=Value(3),
                ),
                When(
                    pk__in=destaque_ids,
                    then=Value(2),
                ),
                default=Value(1),
                output_field=IntegerField(),
            )
        )
        .order_by(
            "-prioridade_comercial",
            "-destaque",
            "nome",
        )
    )


def _aplicar_plano_empresa(
    empresa,
):

    premium_ids, destaque_ids = (
        _ids_por_prioridade_comercial(
            "empresa"
        )
    )

    if empresa.pk in premium_ids:
        empresa.prioridade_comercial = 3

    elif empresa.pk in destaque_ids:
        empresa.prioridade_comercial = 2

    else:
        empresa.prioridade_comercial = 1

    return empresa


def _aplicar_plano_profissional(
    profissional,
):

    premium_ids, destaque_ids = (
        _ids_por_prioridade_comercial(
            "profissional"
        )
    )

    if profissional.pk in premium_ids:
        profissional.prioridade_comercial = 3

    elif profissional.pk in destaque_ids:
        profissional.prioridade_comercial = 2

    else:
        profissional.prioridade_comercial = 1

    return profissional


def home(request):

    busca = request.GET.get(
        "q",
        "",
    ).strip()

    cidade_slug = request.GET.get(
        "cidade",
        "",
    ).strip()

    categoria_slug = request.GET.get(
        "categoria",
        "",
    ).strip()

    tipo = request.GET.get(
        "tipo",
        "",
    ).strip()

    cidades = Cidade.objects.filter(
        ativa=True
    ).order_by(
        "nome"
    )

    categorias = Categoria.objects.filter(
        ativa=True
    ).order_by(
        "nome"
    )

    empresas = (
        Empresa.objects
        .filter(
            ativa=True
        )
        .select_related(
            "cidade",
            "categoria",
        )
    )

    profissionais = (
        Profissional.objects
        .filter(
            ativo=True
        )
        .select_related(
            "cidade",
            "categoria",
            "empresa",
        )
    )

    if busca:

        empresas = empresas.filter(
            Q(
                nome_fantasia__icontains=busca
            )
            | Q(
                descricao__icontains=busca
            )
            | Q(
                endereco__icontains=busca
            )
            | Q(
                bairro__icontains=busca
            )
            | Q(
                categoria__nome__icontains=busca
            )
            | Q(
                cidade__nome__icontains=busca
            )
        )

        profissionais = profissionais.filter(
            Q(
                nome__icontains=busca
            )
            | Q(
                especialidade__icontains=busca
            )
            | Q(
                descricao__icontains=busca
            )
            | Q(
                endereco__icontains=busca
            )
            | Q(
                bairro__icontains=busca
            )
            | Q(
                categoria__nome__icontains=busca
            )
            | Q(
                cidade__nome__icontains=busca
            )
        )

    if cidade_slug:

        empresas = empresas.filter(
            cidade__slug=cidade_slug
        )

        profissionais = profissionais.filter(
            cidade__slug=cidade_slug
        )

    if categoria_slug:

        empresas = empresas.filter(
            categoria__slug=categoria_slug
        )

        profissionais = profissionais.filter(
            categoria__slug=categoria_slug
        )

    if tipo == "empresas":

        profissionais = profissionais.none()

    elif tipo == "profissionais":

        empresas = empresas.none()

    empresas = _ordenar_empresas(
        empresas
    )

    profissionais = _ordenar_profissionais(
        profissionais
    )

    total_empresas = empresas.count()

    total_profissionais = (
        profissionais.count()
    )

    total_resultados = (
        total_empresas
        + total_profissionais
    )

    filtros_ativos = bool(
        busca
        or cidade_slug
        or categoria_slug
        or tipo
    )

    return render(
        request,
        "core/home.html",
        {
            "cidades": cidades,
            "categorias": categorias,
            "empresas": empresas,
            "profissionais": profissionais,
            "busca": busca,
            "cidade_selecionada":
                cidade_slug,
            "categoria_selecionada":
                categoria_slug,
            "tipo_selecionado":
                tipo,
            "total_empresas":
                total_empresas,
            "total_profissionais":
                total_profissionais,
            "total_resultados":
                total_resultados,
            "filtros_ativos":
                filtros_ativos,
        },
    )


def planos(request):

    planos_disponiveis = (
        Plano.objects
        .filter(
            ativo=True
        )
        .order_by(
            "ordem",
            "preco_mensal",
            "nome",
        )
    )

    return render(
        request,
        "core/planos.html",
        {
            "planos":
                planos_disponiveis,
        },
    )


def cidade_home(
    request,
    cidade_slug,
):

    cidade = get_object_or_404(
        Cidade,
        slug=cidade_slug,
        ativa=True,
    )

    busca = request.GET.get(
        "q",
        "",
    ).strip()

    categorias = Categoria.objects.filter(
        ativa=True
    ).order_by(
        "nome"
    )

    empresas = Empresa.objects.filter(
        cidade=cidade,
        ativa=True,
    )

    profissionais = Profissional.objects.filter(
        cidade=cidade,
        ativo=True,
    )

    if busca:

        empresas = empresas.filter(
            Q(
                nome_fantasia__icontains=busca
            )
            | Q(
                descricao__icontains=busca
            )
            | Q(
                endereco__icontains=busca
            )
            | Q(
                bairro__icontains=busca
            )
            | Q(
                categoria__nome__icontains=busca
            )
        )

        profissionais = profissionais.filter(
            Q(
                nome__icontains=busca
            )
            | Q(
                especialidade__icontains=busca
            )
            | Q(
                descricao__icontains=busca
            )
            | Q(
                bairro__icontains=busca
            )
            | Q(
                categoria__nome__icontains=busca
            )
        )

    empresas = _ordenar_empresas(
        empresas
    )

    profissionais = _ordenar_profissionais(
        profissionais
    )

    return render(
        request,
        "core/cidade_home.html",
        {
            "cidade": cidade,
            "categorias": categorias,
            "empresas": empresas,
            "profissionais": profissionais,
            "busca": busca,
        },
    )


def categoria(
    request,
    cidade_slug,
    categoria_slug,
):

    cidade = get_object_or_404(
        Cidade,
        slug=cidade_slug,
        ativa=True,
    )

    categoria_obj = get_object_or_404(
        Categoria,
        slug=categoria_slug,
        ativa=True,
    )

    empresas = Empresa.objects.filter(
        cidade=cidade,
        categoria=categoria_obj,
        ativa=True,
    )

    profissionais = Profissional.objects.filter(
        cidade=cidade,
        categoria=categoria_obj,
        ativo=True,
    )

    empresas = _ordenar_empresas(
        empresas
    )

    profissionais = _ordenar_profissionais(
        profissionais
    )

    return render(
        request,
        "core/categoria.html",
        {
            "cidade": cidade,
            "categoria": categoria_obj,
            "empresas": empresas,
            "profissionais": profissionais,
        },
    )


def empresa_detalhe(
    request,
    cidade_slug,
    empresa_slug,
):

    empresa = get_object_or_404(
        Empresa.objects.select_related(
            "cidade",
            "categoria",
        ),
        cidade__slug=cidade_slug,
        slug=empresa_slug,
        ativa=True,
    )

    empresa = _aplicar_plano_empresa(
        empresa
    )

    relacionadas = (
        Empresa.objects
        .filter(
            cidade=empresa.cidade,
            categoria=empresa.categoria,
            ativa=True,
        )
        .exclude(
            pk=empresa.pk
        )
    )

    relacionadas = _ordenar_empresas(
        relacionadas
    )[:6]

    avaliacoes_aprovadas = (
        empresa.avaliacoes
        .filter(aprovado=True)
        .order_by("-criado_em")
    )

    media_avaliacoes = (
        avaliacoes_aprovadas
        .aggregate(media=Avg("nota"))["media"]
        or 0
    )

    total_avaliacoes = avaliacoes_aprovadas.count()

    return render(
        request,
        "core/empresa_detalhe.html",
        {
            "empresa": empresa,
            "relacionadas": relacionadas,
            "avaliacoes_aprovadas": avaliacoes_aprovadas[:10],
            "media_avaliacoes": media_avaliacoes,
            "total_avaliacoes": total_avaliacoes,
        },
    )


def profissional_detalhe(
    request,
    cidade_slug,
    profissional_slug,
):

    profissional = get_object_or_404(
        Profissional.objects.select_related(
            "cidade",
            "categoria",
            "empresa",
        ),
        cidade__slug=cidade_slug,
        slug=profissional_slug,
        ativo=True,
    )

    profissional = (
        _aplicar_plano_profissional(
            profissional
        )
    )

    relacionados = (
        Profissional.objects
        .filter(
            cidade=profissional.cidade,
            categoria=profissional.categoria,
            ativo=True,
        )
        .exclude(
            pk=profissional.pk
        )
    )

    relacionados = (
        _ordenar_profissionais(
            relacionados
        )[:6]
    )

    avaliacoes_aprovadas = (
        profissional.avaliacoes
        .filter(aprovado=True)
        .order_by("-criado_em")
    )

    media_avaliacoes = (
        avaliacoes_aprovadas
        .aggregate(media=Avg("nota"))["media"]
        or 0
    )

    total_avaliacoes = avaliacoes_aprovadas.count()

    return render(
        request,
        "core/profissional_detalhe.html",
        {
            "profissional": profissional,
            "relacionados": relacionados,
            "avaliacoes_aprovadas": avaliacoes_aprovadas[:10],
            "media_avaliacoes": media_avaliacoes,
            "total_avaliacoes": total_avaliacoes,
        },
    )


@login_required
def minha_conta(request):

    hoje = timezone.localdate()

    empresas = (
        Empresa.objects
        .filter(
            usuario=request.user,
        )
        .select_related(
            "cidade",
            "categoria",
        )
        .order_by(
            "nome_fantasia"
        )
    )

    profissionais = (
        Profissional.objects
        .filter(
            usuario=request.user,
        )
        .select_related(
            "cidade",
            "categoria",
            "empresa",
        )
        .order_by(
            "nome"
        )
    )

    empresas_cliente = []

    for empresa in empresas:

        assinatura = (
            Assinatura.objects
            .select_related(
                "plano"
            )
            .filter(
                empresa=empresa,
                profissional__isnull=True,
                status=Assinatura.STATUS_ATIVA,
                inicio__lte=hoje,
                plano__ativo=True,
            )
            .filter(
                Q(
                    vencimento__isnull=True
                )
                | Q(
                    vencimento__gte=hoje
                )
            )
            .order_by(
                "-inicio",
                "-criada_em",
            )
            .first()
        )

        plano = (
            assinatura.plano
            if assinatura
            else None
        )

        dias_restantes = None

        if (
            assinatura
            and assinatura.vencimento
        ):
            dias_restantes = max(
                (
                    assinatura.vencimento
                    - hoje
                ).days,
                0,
            )

        renovacao_programada = (
            Assinatura.objects
            .select_related(
                "plano"
            )
            .filter(
                empresa=empresa,
                profissional__isnull=True,
                status=Assinatura.STATUS_ATIVA,
                inicio__gt=hoje,
                plano__ativo=True,
            )
            .order_by(
                "inicio",
                "criada_em",
            )
            .first()
        )
        pedido_pendente = (
            PedidoFinanceiro.objects
            .select_related(
                "plano"
            )
            .filter(
                empresa=empresa,
                profissional__isnull=True,
                status=PedidoFinanceiro.STATUS_PENDENTE,
            )
            .order_by(
                "-criado_em"
            )
            .first()
        )
        empresas_cliente.append(
           {
                "objeto": empresa,
                "plano": plano,
                "assinatura":
                    assinatura,
                "dias_restantes":
                    dias_restantes,
                "renovacao_programada":
                    renovacao_programada,
                "pedido_pendente":
                    pedido_pendente,
            }
        )
        
    profissionais_cliente = []

    for profissional in profissionais:

        assinatura = (
            Assinatura.objects
            .select_related(
                "plano"
            )
            .filter(
                profissional=profissional,
                empresa__isnull=True,
                status=Assinatura.STATUS_ATIVA,
                inicio__lte=hoje,
                plano__ativo=True,
            )
            .filter(
                Q(
                    vencimento__isnull=True
                )
                | Q(
                    vencimento__gte=hoje
                )
            )
            .order_by(
                "-inicio",
                "-criada_em",
            )
            .first()
        )

        plano = (
            assinatura.plano
            if assinatura
            else None
        )

        dias_restantes = None

        if (
            assinatura
            and assinatura.vencimento
        ):
            dias_restantes = max(
                (
                    assinatura.vencimento
                    - hoje
                ).days,
                0,
            )

        renovacao_programada = (
            Assinatura.objects
            .select_related(
                "plano"
            )
            .filter(
                profissional=profissional,
                empresa__isnull=True,
                status=Assinatura.STATUS_ATIVA,
                inicio__gt=hoje,
                plano__ativo=True,
            )
            .order_by(
                "inicio",
                "criada_em",
            )
            .first()
        )
        pedido_pendente = (
            PedidoFinanceiro.objects
            .select_related(
                "plano"
            )
            .filter(
                profissional=profissional,
                empresa__isnull=True,
                status=PedidoFinanceiro.STATUS_PENDENTE,
            )
            .order_by(
                "-criado_em"
            )
            .first()
        )
        profissionais_cliente.append(
             {
                "objeto":
                    profissional,
                "plano":
                    plano,
                "assinatura":
                    assinatura,
                "dias_restantes":
                    dias_restantes,
                "renovacao_programada":
                    renovacao_programada,
                "pedido_pendente":
                    pedido_pendente,
            }
        )
        

    return render(
        request,
        "core/minha_conta.html",
        {
            "empresas_cliente":
                empresas_cliente,
            "profissionais_cliente":
                profissionais_cliente,
        },
    )


@login_required
def selecionar_plano(
    request,
    plano_id,
):

    plano = get_object_or_404(
        Plano,
        pk=plano_id,
        ativo=True,
    )

    empresas = (
        Empresa.objects
        .filter(
            usuario=request.user,
            ativa=True,
        )
        .select_related(
            "cidade",
        )
        .order_by(
            "nome_fantasia"
        )
    )

    profissionais = (
        Profissional.objects
        .filter(
            usuario=request.user,
            ativo=True,
        )
        .select_related(
            "cidade",
        )
        .order_by(
            "nome"
        )
    )

    if (
        not empresas.exists()
        and not profissionais.exists()
    ):

        messages.warning(
            request,
            "Sua conta ainda n├úo possui uma "
            "empresa ou profissional vinculado."
        )

        return redirect(
            "core:minha_conta"
        )

    return render(
        request,
        "core/selecionar_plano.html",
        {
            "plano": plano,
            "empresas": empresas,
            "profissionais":
                profissionais,
        },
    )


@login_required
def alterar_plano_empresa(
    request,
    plano_id,
    empresa_id,
):

    if request.method != "POST":

        return redirect(
            "core:selecionar_plano",
            plano_id=plano_id,
        )

    plano = get_object_or_404(
        Plano,
        pk=plano_id,
        ativo=True,
    )

    empresa = get_object_or_404(
        Empresa,
        pk=empresa_id,
        usuario=request.user,
        ativa=True,
    )

    pedido = PedidoFinanceiro.objects.create(
        empresa=empresa,
        plano=plano,
        valor=plano.preco_mensal,
        status=PedidoFinanceiro.STATUS_PENDENTE,
    )

    return redirect(
        "financeiro:pagamento",
        pedido_id=pedido.pk,
    )
              
               
@login_required
def alterar_plano_profissional(
    request,
    plano_id,
    profissional_id,
):

    if request.method != "POST":

        return redirect(
            "core:selecionar_plano",
            plano_id=plano_id,
        )

    plano = get_object_or_404(
        Plano,
        pk=plano_id,
        ativo=True,
    )

    profissional = get_object_or_404(
        Profissional,
        pk=profissional_id,
        usuario=request.user,
        ativo=True,
    )

    assinatura_atual = assinatura_vigente(
        profissional=profissional
    )

    if (
        assinatura_atual
        and assinatura_atual.plano_id
        == plano.id
    ):

        messages.info(
            request,
            (
                f"O profissional "
                f"{profissional.nome} "
                f"já utiliza o plano "
                f"{plano.nome}."
            ),
        )

        return redirect(
            "core:minha_conta"
        )

    pedido = PedidoFinanceiro.objects.create(
        empresa=None,
        profissional=profissional,
        plano=plano,
        valor=plano.preco_mensal,
        status=PedidoFinanceiro.STATUS_PENDENTE,
    )

    return redirect(
        "financeiro:pagamento",
        pedido_id=pedido.pk,
    )


@login_required
def editar_empresa(
    request,
    empresa_id,
):

    empresa = get_object_or_404(
        Empresa.objects.select_related(
            "cidade",
            "categoria",
        ),
        pk=empresa_id,
        usuario=request.user,
    )

    if request.method == "POST":

        form = EmpresaClienteForm(
            request.POST,
            request.FILES,
            instance=empresa,
        )

        if form.is_valid():

            form.save()

            messages.success(
                request,
                "Dados da empresa atualizados com sucesso.",
            )

            return redirect(
                "core:minha_conta"
            )

    else:

        form = EmpresaClienteForm(
            instance=empresa,
        )

    return render(
        request,
        "core/editar_empresa.html",
        {
            "form": form,
            "empresa": empresa,
        },
    )


@login_required
def editar_profissional(
    request,
    profissional_id,
):

    profissional = get_object_or_404(
        Profissional.objects.select_related(
            "cidade",
            "categoria",
            "empresa",
        ),
        pk=profissional_id,
        usuario=request.user,
    )

    if request.method == "POST":

        form = ProfissionalClienteForm(
            request.POST,
            request.FILES,
            instance=profissional,
        )

        if form.is_valid():

            form.save()

            messages.success(
                request,
                "Dados do perfil profissional atualizados com sucesso.",
            )

            return redirect(
                "core:minha_conta"
            )

    else:

        form = ProfissionalClienteForm(
            instance=profissional,
        )

    return render(
        request,
        "core/editar_profissional.html",
        {
            "form": form,
            "profissional": profissional,
        },
    )@login_required
def alterar_renovacao_automatica(
    request,
    assinatura_id,
):

    if request.method != "POST":

        return redirect(
            "core:minha_conta"
        )

    assinatura = get_object_or_404(
        Assinatura,
        pk=assinatura_id,
        status=Assinatura.STATUS_ATIVA,
    )

    pertence_usuario = False

    if (
        assinatura.empresa
        and assinatura.empresa.usuario_id
        == request.user.id
    ):
        pertence_usuario = True

    if (
        assinatura.profissional
        and assinatura.profissional.usuario_id
        == request.user.id
    ):
        pertence_usuario = True

    if not pertence_usuario:

        raise Http404

    assinatura.renovacao_automatica = (
        not assinatura.renovacao_automatica
    )

    assinatura.save(
        update_fields=[
            "renovacao_automatica",
        ]
    )

    if assinatura.renovacao_automatica:

        messages.success(
            request,
            "Renovação automática ativada.",
        )

    else:

        messages.success(
            request,
            "Renovação automática desativada.",
        )

    return redirect(
        "core:minha_conta"
    )
