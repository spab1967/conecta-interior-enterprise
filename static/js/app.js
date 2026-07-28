"use strict";

if ("serviceWorker" in navigator) {
    window.addEventListener("load", () => {
        navigator.serviceWorker.register(
            "/service-worker.js",
            {scope: "/"}
        ).catch(() => {
            // O site continua funcionando normalmente sem o modo instalável.
        });
    });
}


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
