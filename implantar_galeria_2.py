from pathlib import Path


CAMINHO = Path("apps/core/views.py")

texto = CAMINHO.read_text(encoding="utf-8")


# ============================================================
# 1. IMPORTS DOS MODELOS DE GALERIA
# ============================================================

texto = texto.replace(
    "from apps.empresas.models import Empresa",
    "from apps.empresas.models import Empresa, FotoEmpresa",
)

texto = texto.replace(
    "from apps.profissionais.models import Profissional",
    "from apps.profissionais.models import Profissional, FotoProfissional",
)


# ============================================================
# 2. IMPORT DO LIMITE DE FOTOS
# ============================================================

texto = texto.replace(
    """from apps.planos.services import (
    assinatura_vigente,
    plano_vigente,
)""",
    """from apps.planos.services import (
    assinatura_vigente,
    plano_vigente,
    limite_fotos,
)""",
)


# ============================================================
# 3. SUBSTITUIR EDITAR EMPRESA
# ============================================================

inicio = texto.index(
    "@login_required\ndef editar_empresa("
)

fim = texto.index(
    "@login_required\ndef editar_profissional(",
    inicio,
)

novo_editar_empresa = '''@login_required
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


'''

texto = (
    texto[:inicio]
    + novo_editar_empresa
    + texto[fim:]
)


# ============================================================
# 4. SUBSTITUIR EDITAR PROFISSIONAL
# ============================================================

inicio = texto.index(
    "@login_required\ndef editar_profissional("
)

fim = texto.index(
    "@login_required\ndef alterar_renovacao_automatica(",
    inicio,
)

novo_editar_profissional = '''@login_required
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


'''

texto = (
    texto[:inicio]
    + novo_editar_profissional
    + texto[fim:]
)


CAMINHO.write_text(
    texto,
    encoding="utf-8",
)

print(
    "ETAPA 2 DA GALERIA CONCLUIDA."
)