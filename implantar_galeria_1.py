from pathlib import Path


def alterar_empresa():
    caminho = Path("apps/empresas/models.py")
    texto = caminho.read_text(encoding="utf-8")

    if "class FotoEmpresa(models.Model):" in texto:
        print("FotoEmpresa ja existe.")
        return

    bloco = r'''


class FotoEmpresa(models.Model):

    empresa = models.ForeignKey(
        Empresa,
        on_delete=models.CASCADE,
        related_name="galeria",
    )

    imagem = models.ImageField(
        upload_to="empresas/galeria/",
    )

    ordem = models.PositiveIntegerField(
        default=0,
    )

    criada_em = models.DateTimeField(
        auto_now_add=True,
    )

    class Meta:
        ordering = [
            "ordem",
            "id",
        ]

        verbose_name = "Foto da empresa"
        verbose_name_plural = "Fotos da empresa"

    def __str__(self):
        return f"Foto de {self.empresa.nome_fantasia}"
'''

    texto = texto.rstrip() + bloco + "\n"
    caminho.write_text(texto, encoding="utf-8")

    print("FotoEmpresa criada com sucesso.")


def alterar_profissional():
    caminho = Path("apps/profissionais/models.py")
    texto = caminho.read_text(encoding="utf-8")

    if "class FotoProfissional(models.Model):" in texto:
        print("FotoProfissional ja existe.")
        return

    bloco = r'''


class FotoProfissional(models.Model):

    profissional = models.ForeignKey(
        Profissional,
        on_delete=models.CASCADE,
        related_name="galeria",
    )

    imagem = models.ImageField(
        upload_to="profissionais/galeria/",
    )

    ordem = models.PositiveIntegerField(
        default=0,
    )

    criada_em = models.DateTimeField(
        auto_now_add=True,
    )

    class Meta:
        ordering = [
            "ordem",
            "id",
        ]

        verbose_name = "Foto do profissional"
        verbose_name_plural = "Fotos do profissional"

    def __str__(self):
        return f"Foto de {self.profissional.nome}"
'''

    texto = texto.rstrip() + bloco + "\n"
    caminho.write_text(texto, encoding="utf-8")

    print("FotoProfissional criada com sucesso.")


if __name__ == "__main__":
    alterar_empresa()
    alterar_profissional()
    print("ETAPA 1 DA GALERIA CONCLUIDA.")