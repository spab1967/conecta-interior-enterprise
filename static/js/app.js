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
