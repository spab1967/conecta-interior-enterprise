import django.db.models.deletion
from django.db import migrations, models
from django.db.models import Q


class Migration(migrations.Migration):

    dependencies = [
        ("profissionais", "0003_profissional_usuario"),
        ("servicos", "0001_initial"),
    ]

    operations = [
        migrations.AlterField(
            model_name="servico",
            name="empresa",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.CASCADE,
                related_name="servicos",
                to="empresas.empresa",
            ),
        ),
        migrations.AddField(
            model_name="servico",
            name="profissional",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.CASCADE,
                related_name="servicos",
                to="profissionais.profissional",
            ),
        ),
        migrations.AlterField(
            model_name="servico",
            name="cidade",
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.CASCADE,
                related_name="servicos",
                to="cidades.cidade",
            ),
        ),
        migrations.AddConstraint(
            model_name="servico",
            constraint=models.CheckConstraint(
                condition=(
                    Q(empresa__isnull=False, profissional__isnull=True)
                    | Q(empresa__isnull=True, profissional__isnull=False)
                ),
                name="servico_um_titular",
            ),
        ),
    ]
