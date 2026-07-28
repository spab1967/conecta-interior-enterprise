from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import include, path
from django_ratelimit.decorators import ratelimit


admin.site.login = ratelimit(
    key="post:username",
    rate="5/5m",
    method="POST",
    block=True,
)(admin.site.login)


urlpatterns = [
    path(
        "servicos/",
        include("apps.servicos.urls"),
    ),

    path("admin/", admin.site.urls),

    path(
        "administracao/",
        include("apps.administracao.urls"),
    ),

    path(
        "empresas/",
        include("apps.empresas.urls"),
    ),

    path(
        "favoritos/",
        include("apps.favoritos.urls"),
    ),

    path(
        "cadastros/",
        include("apps.cadastros.urls"),
    ),

    path(
        "avaliacoes/",
        include("apps.avaliacoes.urls"),
    ),

    path(
        "financeiro/",
        include("apps.financeiro.urls"),
    ),

    path(
        "metricas/",
        include("apps.metricas.urls"),
    ),

    path(
        "",
        include("apps.core.urls"),
    ),
]


if settings.DEBUG:
    urlpatterns += static(
        settings.MEDIA_URL,
        document_root=settings.MEDIA_ROOT,
    )