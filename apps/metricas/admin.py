from datetime import timedelta

from django.contrib import admin
from django.db.models import Count
from django.urls import reverse
from django.utils import timezone
from django.utils.html import format_html

from .models import EventoContato


@admin.register(EventoContato)
class EventoContatoAdmin(admin.ModelAdmin):

    list_display = (
        "id",
        "tipo",
        "destino",
        "cidade",
        "criado_em",
    )

    list_filter = (
        "tipo",
        "criado_em",
        "empresa__cidade",
        "profissional__cidade",
    )

    search_fields = (
        "empresa__nome_fantasia",
        "profissional__nome",
        "empresa__cidade__nome",
        "profissional__cidade__nome",
    )

    readonly_fields = (
        "empresa",
        "profissional",
        "tipo",
        "criado_em",
    )

    ordering = (
        "-criado_em",
    )

    date_hierarchy = "criado_em"

    list_per_page = 50

    def has_add_permission(self, request):
        return False

    def has_change_permission(
        self,
        request,
        obj=None,
    ):
        return False

    @admin.display(description="Destino")
    def destino(self, obj):

        if obj.empresa:

            url = reverse(
                "admin:empresas_empresa_change",
                args=[obj.empresa.pk],
            )

            return format_html(
                '<a href="{}">{}</a>',
                url,
                obj.empresa.nome_fantasia,
            )

        if obj.profissional:

            url = reverse(
                "admin:profissionais_profissional_change",
                args=[obj.profissional.pk],
            )

            return format_html(
                '<a href="{}">{}</a>',
                url,
                obj.profissional.nome,
            )

        return "-"

    @admin.display(description="Cidade")
    def cidade(self, obj):

        if obj.empresa:
            return obj.empresa.cidade.nome

        if obj.profissional:
            return obj.profissional.cidade.nome

        return "-"

    def changelist_view(
        self,
        request,
        extra_context=None,
    ):

        queryset = self.get_queryset(
            request
        )

        agora = timezone.now()
        hoje = timezone.localdate()

        inicio_hoje = timezone.make_aware(
            timezone.datetime.combine(
                hoje,
                timezone.datetime.min.time(),
            )
        )

        inicio_7_dias = agora - timedelta(
            days=7
        )

        inicio_30_dias = agora - timedelta(
            days=30
        )

        total = queryset.count()

        total_hoje = queryset.filter(
            criado_em__gte=inicio_hoje
        ).count()

        total_7_dias = queryset.filter(
            criado_em__gte=inicio_7_dias
        ).count()

        total_30_dias = queryset.filter(
            criado_em__gte=inicio_30_dias
        ).count()

        whatsapp = queryset.filter(
            tipo=EventoContato.TIPO_WHATSAPP
        ).count()

        telefone = queryset.filter(
            tipo=EventoContato.TIPO_TELEFONE
        ).count()

        email = queryset.filter(
            tipo=EventoContato.TIPO_EMAIL
        ).count()

        site = queryset.filter(
            tipo=EventoContato.TIPO_SITE
        ).count()

        instagram = queryset.filter(
            tipo=EventoContato.TIPO_INSTAGRAM
        ).count()

        canais_30_dias = {
            "whatsapp": queryset.filter(
                tipo=EventoContato.TIPO_WHATSAPP,
                criado_em__gte=inicio_30_dias,
            ).count(),

            "telefone": queryset.filter(
                tipo=EventoContato.TIPO_TELEFONE,
                criado_em__gte=inicio_30_dias,
            ).count(),

            "email": queryset.filter(
                tipo=EventoContato.TIPO_EMAIL,
                criado_em__gte=inicio_30_dias,
            ).count(),

            "site": queryset.filter(
                tipo=EventoContato.TIPO_SITE,
                criado_em__gte=inicio_30_dias,
            ).count(),

            "instagram": queryset.filter(
                tipo=EventoContato.TIPO_INSTAGRAM,
                criado_em__gte=inicio_30_dias,
            ).count(),
        }

        empresas = (
            queryset
            .filter(
                empresa__isnull=False
            )
            .values(
                "empresa__id",
                "empresa__nome_fantasia",
                "empresa__cidade__nome",
            )
            .annotate(
                total=Count("id")
            )
            .order_by(
                "-total",
                "empresa__nome_fantasia",
            )[:10]
        )

        profissionais = (
            queryset
            .filter(
                profissional__isnull=False
            )
            .values(
                "profissional__id",
                "profissional__nome",
                "profissional__cidade__nome",
            )
            .annotate(
                total=Count("id")
            )
            .order_by(
                "-total",
                "profissional__nome",
            )[:10]
        )

        ranking_empresas_30_dias = (
            queryset
            .filter(
                empresa__isnull=False,
                criado_em__gte=inicio_30_dias,
            )
            .values(
                "empresa__nome_fantasia",
                "empresa__cidade__nome",
            )
            .annotate(
                total=Count("id")
            )
            .order_by(
                "-total",
                "empresa__nome_fantasia",
            )[:10]
        )

        ranking_profissionais_30_dias = (
            queryset
            .filter(
                profissional__isnull=False,
                criado_em__gte=inicio_30_dias,
            )
            .values(
                "profissional__nome",
                "profissional__cidade__nome",
            )
            .annotate(
                total=Count("id")
            )
            .order_by(
                "-total",
                "profissional__nome",
            )[:10]
        )

        extra_context = (
            extra_context or {}
        )

        extra_context.update(
            {
                "metricas_total": total,
                "metricas_hoje": total_hoje,
                "metricas_7_dias": total_7_dias,
                "metricas_30_dias": total_30_dias,

                "metricas_whatsapp": whatsapp,
                "metricas_telefone": telefone,
                "metricas_email": email,
                "metricas_site": site,
                "metricas_instagram": instagram,

                "canais_30_dias": canais_30_dias,

                "ranking_empresas": empresas,
                "ranking_profissionais": profissionais,

                "ranking_empresas_30_dias":
                    ranking_empresas_30_dias,

                "ranking_profissionais_30_dias":
                    ranking_profissionais_30_dias,
            }
        )

        return super().changelist_view(
            request,
            extra_context=extra_context,
        )