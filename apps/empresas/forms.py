from django import forms

from .models import Empresa


class EmpresaClienteForm(forms.ModelForm):

    class Meta:
        model = Empresa

        fields = [
            "nome_fantasia",
            "categoria",
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
        ]

        widgets = {
            "nome_fantasia": forms.TextInput(
                attrs={
                    "class": "form-control",
                }
            ),
            "categoria": forms.Select(
                attrs={
                    "class": "form-select",
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
            "logo": forms.ClearableFileInput(
                attrs={
                    "class": "form-control",
                }
            ),
        }