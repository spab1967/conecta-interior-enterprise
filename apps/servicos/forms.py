from django import forms

from .models import Servico


class ServicoForm(forms.ModelForm):

    class Meta:
        model = Servico
        fields = ("nome", "valor", "ativo")
        widgets = {
            "nome": forms.TextInput(
                attrs={
                    "class": "form-control",
                    "placeholder": "Ex.: Instalação elétrica",
                }
            ),
            "valor": forms.NumberInput(
                attrs={
                    "class": "form-control",
                    "step": "0.01",
                    "min": "0",
                    "placeholder": "Deixe em branco para sob consulta",
                }
            ),
            "ativo": forms.CheckboxInput(
                attrs={"class": "form-check-input"}
            ),
        }
