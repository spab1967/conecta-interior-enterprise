from PIL import Image, UnidentifiedImageError

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import PasswordChangeForm
from django.contrib.auth import update_session_auth_hash
from django.http import Http404, HttpResponse
from django.db import transaction
from django.core.exceptions import ValidationError
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
from django.views.decorators.http import require_POST

from apps.cidades.models import Cidade
from apps.categorias.models import Categoria
from apps.empresas.forms import EmpresaClienteForm
from apps.empresas.models import Empresa, FotoEmpresa
from apps.financeiro.models import PedidoFinanceiro
from apps.planos.models import Assinatura, Plano
from apps.planos.services import (
    assinatura_vigente,
    plano_vigente,
    limite_fotos,
)
from apps.planos.vigencia import calcular_vencimento_plano
from apps.profissionais.forms import ProfissionalClienteForm
from apps.profissionais.models import Profissional, FotoProfissional
from apps.servicos.models import Servico


TAMANHO_MAXIMO_IMAGEM = 5 * 1024 * 1024
FORMATOS_IMAGEM_PERMITIDOS = {"JPEG", "PNG", "WEBP"}


def _validar_imagem_upload(arquivo):
    if not arquivo:
        return

    if arquivo.size > TAMANHO_MAXIMO_IMAGEM:
        raise ValidationError(
            "Cada imagem deve ter no máximo 5 MB."
        )

    try:
        imagem = Image.open(arquivo)
        formato = imagem.format
        imagem.verify()
    except (UnidentifiedImageError, OSError, ValueError):
        raise ValidationError(
            "O arquivo enviado não é uma imagem válida."
        )
    finally:
        arquivo.seek(0)

    if formato not in FORMATOS_IMAGEM_PERMITIDOS:
        raise ValidationError(
            "Envie imagens nos formatos JPG, PNG ou WEBP."
        )


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


def service_worker(request):
    script = """
const CACHE_NAME = "conecta-interior-static-v1";

self.addEventListener("install", () => {
    self.skipWaiting();
});

self.addEventListener("activate", (event) => {
    event.waitUntil(
        caches.keys().then((keys) => Promise.all(
            keys
                .filter((key) => key !== CACHE_NAME)
                .map((key) => caches.delete(key))
        ))
    );
    self.clients.claim();
});

self.addEventListener("fetch", (event) => {
    const request = event.request;
    const url = new URL(request.url);

    if (
        request.method !== "GET"
        || url.origin !== self.location.origin
        || !url.pathname.startsWith("/static/")
    ) {
        return;
    }

    event.respondWith(
        caches.match(request).then((cached) => {
            if (cached) {
                return cached;
            }

            return fetch(request).then((response) => {
                if (response.ok) {
                    const copy = response.clone();
                    caches.open(CACHE_NAME).then((cache) => {
                        cache.put(request, copy);
                    });
                }
                return response;
            });
        })
    );
});
""".strip()

    response = HttpResponse(
        script,
        content_type="application/javascript; charset=utf-8",
    )
    response["Cache-Control"] = "no-cache, no-store, must-revalidate"
    response["Service-Worker-Allowed"] = "/"
    return response


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

        termos = [
            termo
            for termo in busca.split()
            if termo.strip()
        ]

        for termo in termos:

            empresas = empresas.filter(
                Q(nome_fantasia__icontains=termo)
                | Q(descricao__icontains=termo)
                | Q(endereco__icontains=termo)
                | Q(bairro__icontains=termo)
                | Q(categoria__nome__icontains=termo)
                | Q(cidade__nome__icontains=termo)
                | Q(
                    servicos__nome__icontains=termo,
                    servicos__ativo=True,
                )
            ).distinct()

            profissionais = profissionais.filter(
                Q(nome__icontains=termo)
                | Q(especialidade__icontains=termo)
                | Q(descricao__icontains=termo)
                | Q(endereco__icontains=termo)
                | Q(bairro__icontains=termo)
                | Q(categoria__nome__icontains=termo)
                | Q(cidade__nome__icontains=termo)
                | Q(
                    servicos__nome__icontains=termo,
                    servicos__ativo=True,
                )
            ).distinct()

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
def alterar_senha(request):
    if request.method == "POST":
        form = PasswordChangeForm(request.user, request.POST)
        if form.is_valid():
            usuario = form.save()
            update_session_auth_hash(request, usuario)
            messages.success(request, "Senha alterada com sucesso.")
            return redirect("core:minha_conta")
    else:
        form = PasswordChangeForm(request.user)

    return render(
        request,
        "core/alterar_senha.html",
        {"form": form},
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
                valor__gt=0,
                plano__preco_mensal__gt=0,
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
                valor__gt=0,
                plano__preco_mensal__gt=0,
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
@require_POST
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

    assinatura_atual = assinatura_vigente(
        empresa=empresa
    )

    if (
        assinatura_atual
        and assinatura_atual.plano_id
        == plano.id
    ):

        messages.info(
            request,
            (
                f"A empresa "
                f"{empresa.nome_fantasia} "
                f"já utiliza o plano "
                f"{plano.nome}."
            ),
        )

        return redirect(
            "core:minha_conta"
        )

    with transaction.atomic():

        PedidoFinanceiro.objects.filter(
            empresa=empresa,
            profissional__isnull=True,
            status=PedidoFinanceiro.STATUS_PENDENTE,
        ).update(
            status=PedidoFinanceiro.STATUS_CANCELADO,
        )

        if plano.preco_mensal <= 0:

            Assinatura.objects.filter(
                empresa=empresa,
                profissional__isnull=True,
                status=Assinatura.STATUS_ATIVA,
            ).update(
                status=Assinatura.STATUS_CANCELADA,
            )

            Assinatura.objects.create(
                empresa=empresa,
                profissional=None,
                plano=plano,
                status=Assinatura.STATUS_ATIVA,
                inicio=timezone.localdate(),
                vencimento=calcular_vencimento_plano(
                    plano,
                    timezone.localdate(),
                ),
                renovacao_automatica=False,
                observacoes=(
                    "Plano gratuito ativado diretamente "
                    "pelo cliente."
                ),
            )

            messages.success(
                request,
                (
                    f"Plano {plano.nome} ativado "
                    f"para {empresa.nome_fantasia}."
                ),
            )

            return redirect(
                "core:minha_conta"
            )

        pedido = PedidoFinanceiro.objects.create(
            empresa=empresa,
            profissional=None,
            plano=plano,
            valor=plano.preco_mensal,
            status=PedidoFinanceiro.STATUS_PENDENTE,
        )

    return redirect(
        "financeiro:pagamento",
        pedido_id=pedido.pk,
    )

@login_required
@require_POST
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

    with transaction.atomic():

        PedidoFinanceiro.objects.filter(
            profissional=profissional,
            empresa__isnull=True,
            status=PedidoFinanceiro.STATUS_PENDENTE,
        ).update(
            status=PedidoFinanceiro.STATUS_CANCELADO,
        )

        if plano.preco_mensal <= 0:

            Assinatura.objects.filter(
                profissional=profissional,
                empresa__isnull=True,
                status=Assinatura.STATUS_ATIVA,
            ).update(
                status=Assinatura.STATUS_CANCELADA,
            )

            Assinatura.objects.create(
                empresa=None,
                profissional=profissional,
                plano=plano,
                status=Assinatura.STATUS_ATIVA,
                inicio=timezone.localdate(),
                vencimento=calcular_vencimento_plano(
                    plano,
                    timezone.localdate(),
                ),
                renovacao_automatica=False,
                observacoes=(
                    "Plano gratuito ativado diretamente "
                    "pelo cliente."
                ),
            )

            messages.success(
                request,
                (
                    f"Plano {plano.nome} ativado "
                    f"para {profissional.nome}."
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

    limite = limite_fotos(
        empresa=empresa,
    )

    fotos = empresa.galeria.all()

    if request.method == "POST":

        try:
            _validar_imagem_upload(
                request.FILES.get("logo")
            )
            for arquivo in request.FILES.getlist(
                "fotos_galeria"
            ):
                _validar_imagem_upload(arquivo)
        except ValidationError as erro:
            messages.error(request, erro.message)
            return redirect(
                "core:editar_empresa",
                empresa_id=empresa.pk,
            )

        form = EmpresaClienteForm(
            request.POST,
            request.FILES,
            instance=empresa,
        )

        if form.is_valid():

            novas_fotos = request.FILES.getlist(
                "fotos_galeria"
            )

            quantidade_atual = (
                empresa.galeria.count()
            )

            quantidade_final = (
                quantidade_atual
                + len(novas_fotos)
            )

            if quantidade_final > limite:

                messages.error(
                    request,
                    (
                        "O seu plano permite no máximo "
                        f"{limite} foto(s) na galeria. "
                        f"Atualmente existem "
                        f"{quantidade_atual} foto(s)."
                    ),
                )

            else:

                form.save()

                proxima_ordem = (
                    empresa.galeria.count()
                )

                for arquivo in novas_fotos:

                    FotoEmpresa.objects.create(
                        empresa=empresa,
                        imagem=arquivo,
                        ordem=proxima_ordem,
                    )

                    proxima_ordem += 1

                messages.success(
                    request,
                    "Dados da empresa atualizados com sucesso.",
                )

                return redirect(
                    "core:editar_empresa",
                    empresa_id=empresa.pk,
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
            "fotos_galeria": fotos,
            "limite_fotos": limite,
            "quantidade_fotos":
                empresa.galeria.count(),
        },
    )


@login_required
@require_POST
def excluir_foto_empresa(
    request,
    empresa_id,
    foto_id,
):

    if request.method != "POST":

        return redirect(
            "core:editar_empresa",
            empresa_id=empresa_id,
        )

    empresa = get_object_or_404(
        Empresa,
        pk=empresa_id,
        usuario=request.user,
    )

    foto = get_object_or_404(
        FotoEmpresa,
        pk=foto_id,
        empresa=empresa,
    )

    foto.imagem.delete(
        save=False
    )

    foto.delete()

    messages.success(
        request,
        "Foto removida da galeria.",
    )

    return redirect(
        "core:editar_empresa",
        empresa_id=empresa.pk,
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

    limite = limite_fotos(
        profissional=profissional,
    )

    fotos = profissional.galeria.all()

    if request.method == "POST":

        try:
            _validar_imagem_upload(
                request.FILES.get("foto")
            )
            for arquivo in request.FILES.getlist(
                "fotos_galeria"
            ):
                _validar_imagem_upload(arquivo)
        except ValidationError as erro:
            messages.error(request, erro.message)
            return redirect(
                "core:editar_profissional",
                profissional_id=profissional.pk,
            )

        form = ProfissionalClienteForm(
            request.POST,
            request.FILES,
            instance=profissional,
        )

        if form.is_valid():

            novas_fotos = request.FILES.getlist(
                "fotos_galeria"
            )

            quantidade_atual = (
                profissional.galeria.count()
            )

            quantidade_final = (
                quantidade_atual
                + len(novas_fotos)
            )

            if quantidade_final > limite:

                messages.error(
                    request,
                    (
                        "O seu plano permite no máximo "
                        f"{limite} foto(s) na galeria. "
                        f"Atualmente existem "
                        f"{quantidade_atual} foto(s)."
                    ),
                )

            else:

                form.save()

                proxima_ordem = (
                    profissional.galeria.count()
                )

                for arquivo in novas_fotos:

                    FotoProfissional.objects.create(
                        profissional=profissional,
                        imagem=arquivo,
                        ordem=proxima_ordem,
                    )

                    proxima_ordem += 1

                messages.success(
                    request,
                    (
                        "Dados do perfil profissional "
                        "atualizados com sucesso."
                    ),
                )

                return redirect(
                    "core:editar_profissional",
                    profissional_id=profissional.pk,
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
            "fotos_galeria": fotos,
            "limite_fotos": limite,
            "quantidade_fotos":
                profissional.galeria.count(),
        },
    )


@login_required
@require_POST
def excluir_foto_profissional(
    request,
    profissional_id,
    foto_id,
):

    if request.method != "POST":

        return redirect(
            "core:editar_profissional",
            profissional_id=profissional_id,
        )

    profissional = get_object_or_404(
        Profissional,
        pk=profissional_id,
        usuario=request.user,
    )

    foto = get_object_or_404(
        FotoProfissional,
        pk=foto_id,
        profissional=profissional,
    )

    foto.imagem.delete(
        save=False
    )

    foto.delete()

    messages.success(
        request,
        "Foto removida da galeria.",
    )

    return redirect(
        "core:editar_profissional",
        profissional_id=profissional.pk,
    )


@login_required
@require_POST
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
