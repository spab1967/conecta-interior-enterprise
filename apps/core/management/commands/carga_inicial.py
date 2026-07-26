from django.core.management.base import BaseCommand
from apps.cidades.models import Cidade
from apps.categorias.models import Categoria
from apps.empresas.models import Empresa

class Command(BaseCommand):
    help = "Cria cidades, categorias e empresas de demonstração."

    def handle(self, *args, **options):
        categorias = [
            ("Alimentação", "🍽️"), ("Agro", "🚜"), ("Comércio", "🛍️"),
            ("Construção", "🏗️"), ("Educação", "🎓"), ("Farmácias", "💊"),
            ("Mercados", "🛒"), ("Profissionais", "👤"), ("Saúde", "🏥"),
            ("Serviços", "🧰"), ("Turismo", "🧭"), ("Veículos", "🚗"),
        ]
        objetos = {}
        for nome, icone in categorias:
            objetos[nome], _ = Categoria.objects.get_or_create(
                nome=nome, defaults={"icone": icone}
            )

        cidades = {}
        for nome, populacao in [("Abaeté", 24000), ("Paineiras", 4500), ("Martinho Campos", 13000)]:
            cidades[nome], _ = Cidade.objects.get_or_create(
                nome=nome, defaults={"estado": "MG", "populacao": populacao}
            )

        amostras = [
            ("Abaeté", "Mercados", "Mercado Central", "Centro", True),
            ("Abaeté", "Farmácias", "Farmácia Saúde", "Centro", True),
            ("Abaeté", "Alimentação", "Restaurante do Interior", "Centro", False),
            ("Paineiras", "Serviços", "João Eletricista", "Centro", True),
            ("Martinho Campos", "Agro", "Agro Campo Forte", "Centro", True),
        ]
        for cidade, categoria, nome, bairro, destaque in amostras:
            Empresa.objects.get_or_create(
                cidade=cidades[cidade],
                nome_fantasia=nome,
                defaults={
                    "categoria": objetos[categoria],
                    "bairro": bairro,
                    "descricao": "Negócio local cadastrado na plataforma Conecta Interior.",
                    "whatsapp": "37999999999",
                    "destaque": destaque,
                },
            )

        self.stdout.write(self.style.SUCCESS("Carga inicial concluída."))
