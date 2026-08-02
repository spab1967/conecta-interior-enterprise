from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):
    dependencies = [migrations.swappable_dependency(settings.AUTH_USER_MODEL), ("profissionais", "0004_fotoprofissional")]
    operations = [
        migrations.AddField(model_name="profissional", name="liberacao_financeira_ativa", field=models.BooleanField(default=False)),
        migrations.AddField(model_name="profissional", name="liberacao_financeira_ate", field=models.DateField(blank=True, null=True)),
        migrations.AddField(model_name="profissional", name="liberacao_financeira_motivo", field=models.CharField(blank=True, max_length=255)),
        migrations.AddField(model_name="profissional", name="liberacao_financeira_observacao", field=models.TextField(blank=True)),
        migrations.AddField(model_name="profissional", name="liberacao_financeira_em", field=models.DateTimeField(blank=True, null=True)),
        migrations.AddField(model_name="profissional", name="liberacao_financeira_por", field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name="+", to=settings.AUTH_USER_MODEL)),
    ]
