from django.contrib import admin

from .models import Pagamento, PedidoFinanceiro


@admin.register(PedidoFinanceiro)
class PedidoFinanceiroAdmin(
    admin.ModelAdmin
):

    list_display = (
        "id",
        "titular",
        "tipo_titular",
        "plano",
        "valor",
        "status",
        "criado_em",
    )

    list_filter = (
        "status",
        "plano",
        "criado_em",
    )

    search_fields = (
        "empresa__nome_fantasia",
        "profissional__nome",
        "plano__nome",
    )

    autocomplete_fields = (
        "empresa",
        "profissional",
        "plano",
        "assinatura",
    )

    readonly_fields = (
        "criado_em",
        "atualizado_em",
    )

    fieldsets = (
        (
            "Titular",
            {
                "fields": (
                    "empresa",
                    "profissional",
                )
            },
        ),
        (
            "Contratação",
            {
                "fields": (
                    "plano",
                    "assinatura",
                    "valor",
                    "status",
                    "observacoes",
                )
            },
        ),
        (
            "Controle",
            {
                "fields": (
                    "criado_em",
                    "atualizado_em",
                )
            },
        ),
    )


@admin.register(Pagamento)
class PagamentoAdmin(
    admin.ModelAdmin
):

    list_display = (
        "id",
        "pedido",
        "tipo",
        "status",
        "valor",
        "pago_em",
        "criado_em",
    )

    list_filter = (
        "tipo",
        "status",
        "criado_em",
    )

    search_fields = (
        "codigo_transacao",
        "pedido__empresa__nome_fantasia",
        "pedido__profissional__nome",
        "pedido__plano__nome",
    )

    autocomplete_fields = (
        "pedido",
    )

    readonly_fields = (
        "criado_em",
        "atualizado_em",
        "pago_em",
    )

    fieldsets = (
        (
            "Pedido",
            {
                "fields": (
                    "pedido",
                    "valor",
                )
            },
        ),
        (
            "Pagamento",
            {
                "fields": (
                    "tipo",
                    "status",
                    "codigo_transacao",
                    "pago_em",
                )
            },
        ),
        (
            "Controle",
            {
                "fields": (
                    "criado_em",
                    "atualizado_em",
                )
            },
        ),
    )