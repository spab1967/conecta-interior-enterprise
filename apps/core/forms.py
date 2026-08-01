from django import forms

from apps.cadastros.forms import ESPECIALIDADES_SERVICOS
from apps.empresas.models import Empresa
from apps.profissionais.models import Profissional


class EmpresaClienteForm(forms.ModelForm):

    class Meta:
        model = Empresa

        fields = (
            "nome_fantasia",
            "descricao",
            "endereco",
            "bairro",
            "telefone",
            "whatsapp",
            "email",
            "instagram",
            "site",
            "horario",
            "logo",
        )

        widgets = {
            "nome_fantasia": forms.TextInput(
                attrs={"class": "form-control"}
            ),
            "descricao": forms.Textarea(
                attrs={
                    "class": "form-control",
                    "rows": 5,
                }
            ),
            "endereco": forms.TextInput(
                attrs={"class": "form-control"}
            ),
            "bairro": forms.TextInput(
                attrs={"class": "form-control"}
            ),
            "telefone": forms.TextInput(
                attrs={"class": "form-control"}
            ),
            "whatsapp": forms.TextInput(
                attrs={"class": "form-control"}
            ),
            "email": forms.EmailInput(
                attrs={"class": "form-control"}
            ),
            "instagram": forms.URLInput(
                attrs={"class": "form-control"}
            ),
            "site": forms.URLInput(
                attrs={"class": "form-control"}
            ),
            "horario": forms.TextInput(
                attrs={"class": "form-control"}
            ),
            "logo": forms.ClearableFileInput(
                attrs={"class": "form-control"}
            ),
        }


class ProfissionalClienteForm(forms.ModelForm):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.especialidades_servicos = ESPECIALIDADES_SERVICOS

    class Meta:
        model = Profissional

        fields = (
            "nome",
            "especialidade",
            "descricao",
            "endereco",
            "bairro",
            "telefone",
            "whatsapp",
            "email",
            "instagram",
            "site",
            "horario",
            "foto",
            "atendimento_domiciliar",
        )

        widgets = {
            "nome": forms.TextInput(
                attrs={"class": "form-control"}
            ),
            "especialidade": forms.TextInput(
                attrs={
                    "class": "form-control",
                    "list": "especialidades-servicos",
                    "autocomplete": "off",
                }
            ),
            "descricao": forms.Textarea(
                attrs={
                    "class": "form-control",
                    "rows": 5,
                }
            ),
            "endereco": forms.TextInput(
                attrs={"class": "form-control"}
            ),
            "bairro": forms.TextInput(
                attrs={"class": "form-control"}
            ),
            "telefone": forms.TextInput(
                attrs={"class": "form-control"}
            ),
            "whatsapp": forms.TextInput(
                attrs={"class": "form-control"}
            ),
            "email": forms.EmailInput(
                attrs={"class": "form-control"}
            ),
            "instagram": forms.URLInput(
                attrs={"class": "form-control"}
            ),
            "site": forms.URLInput(
                attrs={"class": "form-control"}
            ),
            "horario": forms.TextInput(
                attrs={"class": "form-control"}
            ),
            "foto": forms.ClearableFileInput(
                attrs={"class": "form-control"}
            ),
            "atendimento_domiciliar": forms.CheckboxInput(
                attrs={"class": "form-check-input"}
            ),
        }