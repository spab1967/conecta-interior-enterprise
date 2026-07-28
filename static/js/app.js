"use strict";

let recarregandoAplicativo = false;

function mostrarAtualizacaoAplicativo(registro) {
    if (
        !registro.waiting
        || document.querySelector(".ci-app-update")
    ) {
        return;
    }

    const aviso = document.createElement("div");
    aviso.className = "ci-app-update alert alert-primary shadow";
    aviso.setAttribute("role", "status");
    aviso.innerHTML = [
        "<strong>Nova versão disponível</strong>",
        "<span>Atualize para receber as melhorias mais recentes.</span>",
        '<button type="button" class="btn btn-primary btn-sm">Atualizar</button>'
    ].join("");

    aviso.querySelector("button").addEventListener("click", () => {
        registro.waiting.postMessage("SKIP_WAITING");
    });

    document.body.appendChild(aviso);
}

if ("serviceWorker" in navigator) {
    window.addEventListener("load", () => {
        navigator.serviceWorker.register(
            "/service-worker.js",
            {scope: "/"}
        ).then((registro) => {
            mostrarAtualizacaoAplicativo(registro);

            registro.addEventListener("updatefound", () => {
                const novoWorker = registro.installing;

                if (!novoWorker) {
                    return;
                }

                novoWorker.addEventListener("statechange", () => {
                    if (
                        novoWorker.state === "installed"
                        && navigator.serviceWorker.controller
                    ) {
                        mostrarAtualizacaoAplicativo(registro);
                    }
                });
            });

            registro.update();
        }).catch(() => {
            // O site continua funcionando normalmente sem o modo instalável.
        });

        navigator.serviceWorker.addEventListener(
            "controllerchange",
            () => {
                if (recarregandoAplicativo) {
                    return;
                }

                recarregandoAplicativo = true;
                window.location.reload();
            }
        );
    });
}


let eventoInstalacao = null;

function alternarBotoesInstalacao(visivel) {
    document.querySelectorAll(".js-install-app").forEach((botao) => {
        botao.hidden = !visivel;
    });
}

window.addEventListener("beforeinstallprompt", (evento) => {
    evento.preventDefault();
    eventoInstalacao = evento;
    alternarBotoesInstalacao(true);
});

window.addEventListener("appinstalled", () => {
    eventoInstalacao = null;
    alternarBotoesInstalacao(false);
});

document.addEventListener("click", async (evento) => {
    const botao = evento.target.closest(".js-install-app");

    if (!botao || !eventoInstalacao) {
        return;
    }

    eventoInstalacao.prompt();
    await eventoInstalacao.userChoice;
    eventoInstalacao = null;
    alternarBotoesInstalacao(false);
});


async function copiarLink(url) {
    if (navigator.clipboard && window.isSecureContext) {
        await navigator.clipboard.writeText(url);
        return;
    }

    const campo = document.createElement("textarea");
    campo.value = url;
    campo.setAttribute("readonly", "");
    campo.style.position = "fixed";
    campo.style.opacity = "0";
    document.body.appendChild(campo);
    campo.select();
    document.execCommand("copy");
    campo.remove();
}

async function compartilharPagina(botao) {
    const dados = {
        title: botao.dataset.shareTitle || document.title,
        text: botao.dataset.shareText || "",
        url: window.location.href
    };

    try {
        if (navigator.share) {
            await navigator.share(dados);
            return;
        }

        await copiarLink(dados.url);
        const textoOriginal = botao.textContent;
        botao.textContent = "✓ Link copiado";
        window.setTimeout(() => {
            botao.textContent = textoOriginal;
        }, 2200);
    } catch (erro) {
        if (erro && erro.name === "AbortError") {
            return;
        }

        const textoOriginal = botao.textContent;
        botao.textContent = "Não foi possível compartilhar";
        window.setTimeout(() => {
            botao.textContent = textoOriginal;
        }, 2200);
    }
}

document.addEventListener("click", (evento) => {
    const botao = evento.target.closest(".js-share-page");

    if (botao) {
        compartilharPagina(botao);
    }
});

let avisoConectividade = null;
let aplicativoEsteveOffline = !navigator.onLine;
let temporizadorConectividade = null;

function removerAvisoConectividade() {
    if (temporizadorConectividade) {
        window.clearTimeout(temporizadorConectividade);
        temporizadorConectividade = null;
    }

    if (avisoConectividade) {
        avisoConectividade.remove();
        avisoConectividade = null;
    }
}

function mostrarEstadoConectividade(online) {
    removerAvisoConectividade();

    avisoConectividade = document.createElement("div");
    avisoConectividade.className = [
        "ci-connection-status",
        "alert",
        online ? "alert-success" : "alert-warning",
        "shadow"
    ].join(" ");
    avisoConectividade.setAttribute("role", "status");
    avisoConectividade.setAttribute("aria-live", "polite");

    if (online) {
        avisoConectividade.innerHTML = [
            "<strong>Internet restabelecida</strong>",
            "<span>O aplicativo voltou a funcionar normalmente.</span>"
        ].join("");
    } else {
        avisoConectividade.innerHTML = [
            "<strong>Você está sem internet</strong>",
            "<span>O conteúdo já aberto continua disponível, mas algumas ações podem aguardar a conexão.</span>"
        ].join("");
    }

    document.body.appendChild(avisoConectividade);

    if (online) {
        temporizadorConectividade = window.setTimeout(
            removerAvisoConectividade,
            4000
        );
    }
}

window.addEventListener("offline", () => {
    aplicativoEsteveOffline = true;
    mostrarEstadoConectividade(false);
});

window.addEventListener("online", () => {
    if (aplicativoEsteveOffline) {
        mostrarEstadoConectividade(true);
    }

    aplicativoEsteveOffline = false;
});

if (!navigator.onLine) {
    window.addEventListener("DOMContentLoaded", () => {
        mostrarEstadoConectividade(false);
    });
}
