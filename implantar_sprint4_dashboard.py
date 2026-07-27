from pathlib import Path

arquivo = Path("templates/administracao/dashboard.html")
texto = arquivo.read_text(encoding="utf-8")

marcador = '''        <section class="row g-4 mt-1">

            <div class="col-xl-6">

                <article class="enterprise-panel">

                    <header class="enterprise-panel-header">

                        <h2 class="enterprise-panel-title">
                            Resumo financeiro
                        </h2>'''

novo = '''        <section class="row g-4 mt-1">

            <div class="col-sm-6 col-xl-3">
                <article class="enterprise-metric-card">
                    <div class="enterprise-metric-head">
                        <p class="enterprise-metric-label">
                            Contatos
                        </p>
                    </div>

                    <p class="enterprise-metric-value">
                        {{ total_contatos }}
                    </p>

                    <span class="enterprise-metric-note">
                        {{ contatos_mes }} contatos neste mês
                    </span>
                </article>
            </div>

            <div class="col-sm-6 col-xl-3">
                <article class="enterprise-metric-card">
                    <div class="enterprise-metric-head">
                        <p class="enterprise-metric-label">
                            WhatsApp
                        </p>
                    </div>

                    <p class="enterprise-metric-value">
                        {{ contatos_whatsapp }}
                    </p>

                    <span class="enterprise-metric-note">
                        Conversões por WhatsApp
                    </span>
                </article>
            </div>

            <div class="col-sm-6 col-xl-3">
                <article class="enterprise-metric-card">
                    <div class="enterprise-metric-head">
                        <p class="enterprise-metric-label">
                            Novas empresas
                        </p>
                    </div>

                    <p class="enterprise-metric-value">
                        {{ novas_empresas_mes }}
                    </p>

                    <span class="enterprise-metric-note">
                        Cadastros neste mês
                    </span>
                </article>
            </div>

            <div class="col-sm-6 col-xl-3">
                <article class="enterprise-metric-card">
                    <div class="enterprise-metric-head">
                        <p class="enterprise-metric-label">
                            Novos profissionais
                        </p>
                    </div>

                    <p class="enterprise-metric-value">
                        {{ novos_profissionais_mes }}
                    </p>

                    <span class="enterprise-metric-note">
                        Cadastros neste mês
                    </span>
                </article>
            </div>

        </section>

        <section class="row g-4 mt-1">

            <div class="col-xl-6">

                <article class="enterprise-panel">

                    <header class="enterprise-panel-header">

                        <h2 class="enterprise-panel-title">
                            Resumo financeiro
                        </h2>'''

if marcador not in texto:
    raise SystemExit(
        "ERRO: ponto de insercao do Dashboard nao encontrado."
    )

texto = texto.replace(
    marcador,
    novo,
    1,
)

marcador_estrutura = '''                                <tr>

                                    <th>Pedidos financeiros</th>

                                    <td class="text-end">
                                        {{ total_pedidos }}
                                    </td>

                                </tr>'''

novo_estrutura = '''                                <tr>

                                    <th>Pedidos financeiros</th>

                                    <td class="text-end">
                                        {{ total_pedidos }}
                                    </td>

                                </tr>

                                <tr>

                                    <th>Cadastros neste mês</th>

                                    <td class="text-end">
                                        {{ cadastros_mes }}
                                    </td>

                                </tr>

                                <tr>

                                    <th>Contatos por telefone</th>

                                    <td class="text-end">
                                        {{ contatos_telefone }}
                                    </td>

                                </tr>

                                <tr>

                                    <th>Contatos por e-mail</th>

                                    <td class="text-end">
                                        {{ contatos_email }}
                                    </td>

                                </tr>'''

if marcador_estrutura not in texto:
    raise SystemExit(
        "ERRO: painel Estrutura da Plataforma nao encontrado."
    )

texto = texto.replace(
    marcador_estrutura,
    novo_estrutura,
    1,
)

arquivo.write_text(
    texto,
    encoding="utf-8",
)

print("SPRINT 4 - DASHBOARD EXECUTIVO ATUALIZADO")