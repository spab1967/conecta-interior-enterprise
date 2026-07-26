from django.contrib import messages
from django.shortcuts import get_object_or_404, redirect, render

from apps.empresas.models import Empresa
from apps.profissionais.models import Profissional

from .models import Avaliacao


def avaliar_empresa(request, cidade_slug, empresa_slug):

    empresa = get_object_or_404(
        Empresa,
        cidade__slug=cidade_slug,
        slug=empresa_slug,
        ativa=True,
    )

    if request.method == "POST":

        nome = request.POST.get("nome", "").strip()
        nota = request.POST.get("nota", "").strip()
        comentario = request.POST.get("comentario", "").strip()

        erros = []

        if not nome:
            erros.append("Informe seu nome.")

        if not comentario:
            erros.append("Escreva um comentário.")

        try:
            nota_int = int(nota)

            if nota_int < 1 or nota_int > 5:
                erros.append("A nota deve estar entre 1 e 5.")

        except (TypeError, ValueError):
            nota_int = None
            erros.append("Selecione uma nota entre 1 e 5.")

        if erros:

            return render(
                request,
                "avaliacoes/formulario.html",
                {
                    "tipo": "empresa",
                    "objeto": empresa,
                    "erros": erros,
                    "nome": nome,
                    "nota": nota,
                    "comentario": comentario,
                },
            )

        Avaliacao.objects.create(
            empresa=empresa,
            nome=nome,
            nota=nota_int,
            comentario=comentario,
            aprovado=False,
        )

        messages.success(
            request,
            "Avaliação enviada com sucesso. Ela será publicada após aprovação.",
        )

        return redirect(
            "avaliacoes:sucesso"
        )

    return render(
        request,
        "avaliacoes/formulario.html",
        {
            "tipo": "empresa",
            "objeto": empresa,
        },
    )


def avaliar_profissional(request, cidade_slug, profissional_slug):

    profissional = get_object_or_404(
        Profissional,
        cidade__slug=cidade_slug,
        slug=profissional_slug,
        ativo=True,
    )

    if request.method == "POST":

        nome = request.POST.get("nome", "").strip()
        nota = request.POST.get("nota", "").strip()
        comentario = request.POST.get("comentario", "").strip()

        erros = []

        if not nome:
            erros.append("Informe seu nome.")

        if not comentario:
            erros.append("Escreva um comentário.")

        try:
            nota_int = int(nota)

            if nota_int < 1 or nota_int > 5:
                erros.append("A nota deve estar entre 1 e 5.")

        except (TypeError, ValueError):
            nota_int = None
            erros.append("Selecione uma nota entre 1 e 5.")

        if erros:

            return render(
                request,
                "avaliacoes/formulario.html",
                {
                    "tipo": "profissional",
                    "objeto": profissional,
                    "erros": erros,
                    "nome": nome,
                    "nota": nota,
                    "comentario": comentario,
                },
            )

        Avaliacao.objects.create(
            profissional=profissional,
            nome=nome,
            nota=nota_int,
            comentario=comentario,
            aprovado=False,
        )

        messages.success(
            request,
            "Avaliação enviada com sucesso. Ela será publicada após aprovação.",
        )

        return redirect(
            "avaliacoes:sucesso"
        )

    return render(
        request,
        "avaliacoes/formulario.html",
        {
            "tipo": "profissional",
            "objeto": profissional,
        },
    )


def sucesso(request):

    return render(
        request,
        "avaliacoes/sucesso.html",
    )