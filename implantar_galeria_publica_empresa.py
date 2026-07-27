from pathlib import Path


caminho = Path(
    "templates/core/empresa_detalhe.html"
)

texto = caminho.read_text(
    encoding="utf-8"
)

marcador = """
        {% if empresa.endereco %}
"""

galeria = """
        {% if empresa.galeria.all %}

            <div class="card border-0 shadow-sm mb-4">

                <div class="card-body p-4">

                    <div class="d-flex justify-content-between align-items-center mb-3">

                        <h2 class="h4 fw-bold mb-0">
                            Galeria de fotos
                        </h2>

                        <span class="badge text-bg-light">
                            {{ empresa.galeria.count }}
                            foto{% if empresa.galeria.count != 1 %}s{% endif %}
                        </span>

                    </div>


                    <div class="row g-3">

                        {% for foto in empresa.galeria.all %}

                            <div class="col-6 col-md-4">

                                <a
                                    href="{{ foto.imagem.url }}"
                                    target="_blank"
                                    class="d-block text-decoration-none"
                                >

                                    <img
                                        src="{{ foto.imagem.url }}"
                                        alt="Foto de {{ empresa.nome_fantasia }}"
                                        class="img-fluid rounded shadow-sm w-100"
                                        loading="lazy"
                                        style="
                                            height: 220px;
                                            object-fit: cover;
                                            cursor: pointer;
                                        "
                                    >

                                </a>

                            </div>

                        {% endfor %}

                    </div>

                </div>

            </div>

        {% endif %}


"""

if "Galeria de fotos" in texto:
    print(
        "Galeria publica da empresa ja existe."
    )

elif marcador not in texto:
    raise RuntimeError(
        "Ponto de insercao nao encontrado. "
        "Nenhum arquivo foi alterado."
    )

else:
    texto = texto.replace(
        marcador,
        galeria + marcador,
        1,
    )

    caminho.write_text(
        texto,
        encoding="utf-8",
    )

    print(
        "Galeria publica da empresa implantada."
    )