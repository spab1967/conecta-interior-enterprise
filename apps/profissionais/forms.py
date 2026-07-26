from django import forms

from .models import Profissional


class ProfissionalClienteForm(forms.ModelForm):

    class Meta:
        model = Profissional

        fields = [
            "nome",
            "categoria",
            "empresa",
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
        ]

        widgets = {
            "nome": forms.TextInput(
                attrs={
                    "class": "form-control",
                }
            ),
            "categoria": forms.Select(
                attrs={
                    "class": "form-select",
                }
            ),
            "empresa": forms.Select(
                attrs={
                    "class": "form-select",
                }
            ),
            "especialidade": forms.TextInput(
                attrs={
                    "class": "form-control",
                }
            ),
            "descricao": forms.Textarea(
                attrs={
                    "class": "form-control",
                    "rows": 5,
                }
            ),
            "endereco": forms.TextInput(
                attrs={
                    "class": "form-control",
                }
            ),
            "bairro": forms.TextInput(
                attrs={
                    "class": "form-control",
                }
            ),
            "telefone": forms.TextInput(
                attrs={
                    "class": "form-control",
                }
            ),
            "whatsapp": forms.TextInput(
                attrs={
                    "class": "form-control",
                }
            ),
            "email": forms.EmailInput(
                attrs={
                    "class": "form-control",
                }
            ),
            "instagram": forms.URLInput(
                attrs={
                    "class": "form-control",
                }
            ),
            "site": forms.URLInput(
                attrs={
                    "class": "form-control",
                }
            ),
            "horario": forms.TextInput(
                attrs={
                    "class": "form-control",
                }
            ),
            "foto": forms.ClearableFileInput(
                attrs={
                    "class": "form-control",
                }
            ),
            "atendimento_domiciliar":
                forms.CheckboxInput(
                    attrs={
                        "class":
                            "form-check-input",
                    }
                ),
        }