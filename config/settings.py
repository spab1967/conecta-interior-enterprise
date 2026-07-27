from pathlib import Path
import os

import dj_database_url
from dotenv import load_dotenv


BASE_DIR = Path(__file__).resolve().parent.parent

load_dotenv(BASE_DIR / ".env")


# ============================================================
# CONFIGURACAO PRINCIPAL
# ============================================================

SECRET_KEY = os.getenv(
    "SECRET_KEY",
    "desenvolvimento-conecta-interior-chave-local-segura-2026",
)

DEBUG = os.getenv(
    "DEBUG",
    "True",
).lower() == "true"


ALLOWED_HOSTS = [
    host.strip()
    for host in os.getenv(
        "ALLOWED_HOSTS",
        "127.0.0.1,localhost",
    ).split(",")
    if host.strip()
]


# ============================================================
# APLICACOES
# ============================================================

INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "cloudinary_storage",
    "cloudinary",

    "apps.administracao.apps.AdministracaoConfig",

    "apps.core",
    "apps.cidades",
    "apps.categorias",
    "apps.empresas",
    "apps.profissionais",
    "apps.servicos",
    "apps.avaliacoes",
    "apps.metricas",
    "apps.planos",
    "apps.favoritos",
    "apps.cadastros",
    "apps.financeiro",
]


# ============================================================
# MIDDLEWARE
# ============================================================

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "whitenoise.middleware.WhiteNoiseMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]


ROOT_URLCONF = "config.urls"


# ============================================================
# TEMPLATES
# ============================================================

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [
            BASE_DIR / "templates",
        ],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
        },
    },
]


WSGI_APPLICATION = "config.wsgi.application"

ASGI_APPLICATION = "config.asgi.application"


# ============================================================
# BANCO DE DADOS
# ============================================================

DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "",
).strip()


if DATABASE_URL:

    DATABASES = {
        "default": dj_database_url.parse(
            DATABASE_URL,
            conn_max_age=60,
            conn_health_checks=True,
            ssl_require=True,
        )
    }

else:

    DATABASES = {
        "default": {
            "ENGINE": "django.db.backends.sqlite3",
            "NAME": BASE_DIR / "db.sqlite3",
        }
    }


# ============================================================
# VALIDACAO DE SENHAS
# ============================================================

AUTH_PASSWORD_VALIDATORS = [
    {
        "NAME": (
            "django.contrib.auth.password_validation."
            "UserAttributeSimilarityValidator"
        ),
    },
    {
        "NAME": (
            "django.contrib.auth.password_validation."
            "MinimumLengthValidator"
        ),
    },
    {
        "NAME": (
            "django.contrib.auth.password_validation."
            "CommonPasswordValidator"
        ),
    },
    {
        "NAME": (
            "django.contrib.auth.password_validation."
            "NumericPasswordValidator"
        ),
    },
]


# ============================================================
# INTERNACIONALIZACAO
# ============================================================

LANGUAGE_CODE = "pt-br"

TIME_ZONE = "America/Sao_Paulo"

USE_I18N = True

USE_TZ = True


# ============================================================
# ARQUIVOS ESTATICOS
# ============================================================

STATIC_URL = "static/"

STATICFILES_DIRS = [
    BASE_DIR / "static",
]

STATIC_ROOT = BASE_DIR / "staticfiles"

STATICFILES_STORAGE = (
    "whitenoise.storage."
    "CompressedManifestStaticFilesStorage"
)


# ============================================================
# ARQUIVOS DE MIDIA
# ============================================================

# ============================================================
# CLOUDINARY
# ============================================================

CLOUDINARY_STORAGE = {}

DEFAULT_FILE_STORAGE = (
    "cloudinary_storage.storage.MediaCloudinaryStorage"
)

MEDIA_URL = "/media/"
# ============================================================
# DJANGO
# ============================================================

DEFAULT_AUTO_FIELD = (
    "django.db.models.BigAutoField"
)


# ============================================================
# AUTENTICACAO
# ============================================================

LOGIN_URL = "core:login"

LOGIN_REDIRECT_URL = "core:minha_conta"

LOGOUT_REDIRECT_URL = "core:home"


# ============================================================
# SEGURANCA
#
# DESENVOLVIMENTO:
# valores permanecem False/0 no .env local.
#
# PRODUCAO:
# os valores sao ativados pelo ambiente de hospedagem.
# ============================================================

SECURE_SSL_REDIRECT = os.getenv(
    "SECURE_SSL_REDIRECT",
    "False",
).lower() == "true"


SESSION_COOKIE_SECURE = os.getenv(
    "SESSION_COOKIE_SECURE",
    "False",
).lower() == "true"


CSRF_COOKIE_SECURE = os.getenv(
    "CSRF_COOKIE_SECURE",
    "False",
).lower() == "true"


SECURE_HSTS_SECONDS = int(
    os.getenv(
        "SECURE_HSTS_SECONDS",
        "0",
    )
)


SECURE_HSTS_INCLUDE_SUBDOMAINS = os.getenv(
    "SECURE_HSTS_INCLUDE_SUBDOMAINS",
    "False",
).lower() == "true"


SECURE_HSTS_PRELOAD = os.getenv(
    "SECURE_HSTS_PRELOAD",
    "False",
).lower() == "true"


USE_X_FORWARDED_PROTO = os.getenv(
    "USE_X_FORWARDED_PROTO",
    "False",
).lower() == "true"


if USE_X_FORWARDED_PROTO:
    SECURE_PROXY_SSL_HEADER = (
        "HTTP_X_FORWARDED_PROTO",
        "https",
    )


# ============================================================
# CSRF
# ============================================================

CSRF_TRUSTED_ORIGINS = [
    origem.strip()
    for origem in os.getenv(
        "CSRF_TRUSTED_ORIGINS",
        "",
    ).split(",")
    if origem.strip()
]


# ============================================================
# RENDER
# ============================================================

RENDER_EXTERNAL_HOSTNAME = os.getenv(
    "RENDER_EXTERNAL_HOSTNAME",
    "",
).strip()


if RENDER_EXTERNAL_HOSTNAME:

    if (
        RENDER_EXTERNAL_HOSTNAME
        not in ALLOWED_HOSTS
    ):
        ALLOWED_HOSTS.append(
            RENDER_EXTERNAL_HOSTNAME
        )

    render_origin = (
        f"https://{RENDER_EXTERNAL_HOSTNAME}"
    )

    if (
        render_origin
        not in CSRF_TRUSTED_ORIGINS
    ):
        CSRF_TRUSTED_ORIGINS.append(
            render_origin
        )


# ============================================================
# CONECTA INTERIOR
# CONFIGURACAO FINANCEIRA / PIX
# ============================================================

CONECTA_PIX_FAVORECIDO = os.getenv(
    "CONECTA_PIX_FAVORECIDO",
    "",
)


CONECTA_PIX_CHAVE = os.getenv(
    "CONECTA_PIX_CHAVE",
    "",
)


CONECTA_PIX_BANCO = os.getenv(
    "CONECTA_PIX_BANCO",
    "",
)