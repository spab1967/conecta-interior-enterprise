from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("cidades", "0001_initial"),
    ]

    operations = [
        migrations.AddField(
            model_name="cidade",
            name="atualizada_em",
            field=models.DateTimeField(auto_now=True, verbose_name="atualizada em"),
        ),
        migrations.AddField(
            model_name="cidade",
            name="banner",
            field=models.ImageField(
                blank=True,
                null=True,
                upload_to="cidades/banners/",
                verbose_name="banner municipal",
            ),
        ),
        migrations.AddField(
            model_name="cidade",
            name="cep_principal",
            field=models.CharField(
                blank=True, max_length=9, verbose_name="CEP principal"
            ),
        ),
        migrations.AddField(
            model_name="cidade",
            name="criada_em",
            field=models.DateTimeField(
                auto_now_add=True,
                null=True,
                verbose_name="criada em",
            ),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name="cidade",
            name="ddd",
            field=models.CharField(blank=True, max_length=3, verbose_name="DDD"),
        ),
        migrations.AddField(
            model_name="cidade",
            name="descricao_seo",
            field=models.CharField(
                blank=True, max_length=160, verbose_name="descrição para SEO"
            ),
        ),
        migrations.AddField(
            model_name="cidade",
            name="latitude",
            field=models.DecimalField(
                blank=True,
                decimal_places=7,
                max_digits=10,
                null=True,
                verbose_name="latitude",
            ),
        ),
        migrations.AddField(
            model_name="cidade",
            name="longitude",
            field=models.DecimalField(
                blank=True,
                decimal_places=7,
                max_digits=10,
                null=True,
                verbose_name="longitude",
            ),
        ),
        migrations.AddField(
            model_name="cidade",
            name="site_prefeitura",
            field=models.URLField(blank=True, verbose_name="site da prefeitura"),
        ),
        migrations.AddField(
            model_name="cidade",
            name="telefone_util",
            field=models.CharField(
                blank=True, max_length=30, verbose_name="telefone útil"
            ),
        ),
        migrations.AddField(
            model_name="cidade",
            name="titulo_seo",
            field=models.CharField(
                blank=True, max_length=70, verbose_name="título para SEO"
            ),
        ),
        migrations.AlterField(
            model_name="cidade",
            name="descricao",
            field=models.TextField(blank=True, verbose_name="descrição da cidade"),
        ),
        migrations.AlterField(
            model_name="cidade",
            name="estado",
            field=models.CharField(default="MG", max_length=2, verbose_name="UF"),
        ),
        migrations.AlterField(
            model_name="cidade",
            name="imagem",
            field=models.ImageField(
                blank=True,
                null=True,
                upload_to="cidades/imagens/",
                verbose_name="imagem da cidade",
            ),
        ),
        migrations.AlterField(
            model_name="cidade",
            name="nome",
            field=models.CharField(max_length=120, verbose_name="nome"),
        ),
        migrations.AlterField(
            model_name="cidade",
            name="populacao",
            field=models.PositiveIntegerField(
                blank=True, null=True, verbose_name="população"
            ),
        ),
        migrations.AlterField(
            model_name="cidade",
            name="slug",
            field=models.SlugField(
                blank=True,
                max_length=140,
                unique=True,
                verbose_name="endereço amigável",
            ),
        ),
    ]
