from pathlib import Path

arquivo = Path("apps/administracao/views.py")
texto = arquivo.read_text(encoding="utf-8")

marcador = '''    contexto = {
        "total_empresas": Empresa.objects.count(),'''

novo = '''    eventos_contato = EventoContato.objects.all()

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
        "total_empresas": Empresa.objects.count(),'''

if marcador not in texto:
    raise SystemExit(
        "ERRO: ponto de insercao do Sprint 4 nao encontrado."
    )

texto = texto.replace(marcador, novo, 1)

marcador_contexto = '''        "total_pedidos": PedidoFinanceiro.objects.count(),

        "ultimas_empresas": ('''

novo_contexto = '''        "total_pedidos": PedidoFinanceiro.objects.count(),

        "total_contatos": total_contatos,
        "contatos_mes": contatos_mes,
        "contatos_whatsapp": contatos_whatsapp,
        "contatos_telefone": contatos_telefone,
        "contatos_email": contatos_email,

        "novas_empresas_mes": novas_empresas_mes,
        "novos_profissionais_mes": novos_profissionais_mes,
        "cadastros_mes": cadastros_mes,

        "ultimas_empresas": ('''

if marcador_contexto not in texto:
    raise SystemExit(
        "ERRO: contexto do Dashboard nao encontrado."
    )

texto = texto.replace(
    marcador_contexto,
    novo_contexto,
    1,
)

arquivo.write_text(
    texto,
    encoding="utf-8",
)

print("SPRINT 4 - INDICADORES EXECUTIVOS IMPLANTADOS")