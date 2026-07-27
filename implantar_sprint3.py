from pathlib import Path

arquivo = Path("apps/core/views.py")
texto = arquivo.read_text(encoding="utf-8")

inicio = texto.index("    if busca:\n", texto.index("def home(request):"))
fim = texto.index("    if cidade_slug:\n", inicio)

novo = '''    if busca:

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
                    servico__nome__icontains=termo,
                    servico__ativo=True,
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
                    servico__nome__icontains=termo,
                    servico__ativo=True,
                )
            ).distinct()

'''

texto = texto[:inicio] + novo + texto[fim:]

arquivo.write_text(texto, encoding="utf-8")

print("SPRINT 3 - PESQUISA GLOBAL IMPLANTADA")