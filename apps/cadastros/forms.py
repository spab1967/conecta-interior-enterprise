from django import forms
from django.contrib.auth import get_user_model
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError

from apps.categorias.models import Categoria
from apps.cidades.models import Cidade
from apps.planos.models import Plano

from .models import SolicitacaoCadastro


class SolicitacaoCadastroForm(forms.ModelForm):

    senha = forms.CharField(
        label="Senha",
        strip=False,
        widget=forms.PasswordInput(
            attrs={
                "class": "form-control",
                "autocomplete": "new-password",
                "minlength": "8",
                "placeholder": "Crie uma senha segura",
            }
        ),
    )

    confirmar_senha = forms.CharField(
        label="Confirmar senha",
        strip=False,
        widget=forms.PasswordInput(
            attrs={
                "class": "form-control",
                "autocomplete": "new-password",
                "minlength": "8",
                "placeholder": "Digite novamente a senha",
            }
        ),
    )

    class Meta:

        model = SolicitacaoCadastro

        fields = (
            "plano",
            "tipo",
            "nome",
            "responsavel",
            "cidade",
            "categoria",
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
        )

        widgets = {

            "plano": forms.Select(
                attrs={
                    "class": "form-select",
                }
            ),

            "tipo": forms.Select(
                attrs={
                    "class": "form-select",
                }
            ),

            "nome": forms.TextInput(
                attrs={
                    "class": "form-control",
                    "placeholder":
                        "Nome da empresa ou profissional",
                }
            ),

            "responsavel": forms.TextInput(
                attrs={
                    "class": "form-control",
                    "placeholder":
                        "Nome do responsável",
                }
            ),

            "cidade": forms.Select(
                attrs={
                    "class": "form-select",
                }
            ),

            "categoria": forms.Select(
                attrs={
                    "class": "form-select",
                }
            ),

            "especialidade": forms.TextInput(
                attrs={
                    "class": "form-control",
                    "placeholder":
                        "Ex.: eletricista, pedreiro, manicure",
                }
            ),

            "descricao": forms.Textarea(
                attrs={
                    "class": "form-control",
                    "rows": 5,
                    "placeholder":
                        "Descreva os serviços, produtos ou atividades oferecidas.",
                }
            ),

            "endereco": forms.TextInput(
                attrs={
                    "class": "form-control",
                    "placeholder":
                        "Rua, número e complemento",
                }
            ),

            "bairro": forms.TextInput(
                attrs={
                    "class": "form-control",
                    "placeholder": "Bairro",
                }
            ),

            "telefone": forms.TextInput(
                attrs={
                    "class": "form-control",
                    "placeholder":
                        "(00) 0000-0000",
                }
            ),

            "whatsapp": forms.TextInput(
                attrs={
                    "class": "form-control",
                    "placeholder":
                        "(00) 00000-0000",
                }
            ),

            "email": forms.EmailInput(
                attrs={
                    "class": "form-control",
                    "placeholder":
                        "email@exemplo.com",
                }
            ),

            "instagram": forms.URLInput(
                attrs={
                    "class": "form-control",
                    "placeholder":
                        "https://instagram.com/...",
                }
            ),

            "site": forms.URLInput(
                attrs={
                    "class": "form-control",
                    "placeholder":
                        "https://...",
                }
            ),

            "horario": forms.TextInput(
                attrs={
                    "class": "form-control",
                    "placeholder":
                        "Ex.: Segunda a sexta, 08h às 18h",
                }
            ),
        }

    def __init__(
        self,
        *args,
        plano_inicial=None,
        **kwargs,
    ):

        super().__init__(
            *args,
            **kwargs,
        )

        self.fields["plano"].queryset = (
            Plano.objects
            .filter(
                ativo=True
            )
            .order_by(
                "ordem",
                "preco_mensal",
                "nome",
            )
        )

        self.fields["cidade"].queryset = (
            Cidade.objects
            .filter(
                ativa=True
            )
            .order_by(
                "nome"
            )
        )

        self.fields["categoria"].queryset = (
            Categoria.objects
            .filter(
                ativa=True
            )
            .order_by(
                "nome"
            )
        )

        self.fields["plano"].required = True
        self.fields["categoria"].required = False
        self.fields["responsavel"].required = False
        self.fields["especialidade"].required = False
        self.fields["descricao"].required = False
        self.fields["endereco"].required = False
        self.fields["bairro"].required = False
        self.fields["telefone"].required = False
        self.fields["email"].required = True
        self.fields["instagram"].required = False
        self.fields["site"].required = False
        self.fields["horario"].required = False

        if plano_inicial:

            self.fields["plano"].initial = (
                plano_inicial
            )

    def clean_email(self):

        email = (
            self.cleaned_data.get("email")
            or ""
        ).strip().lower()

        User = get_user_model()

        limite_usuario = User._meta.get_field(
            User.USERNAME_FIELD
        ).max_length

        if limite_usuario and len(email) > limite_usuario:
            raise forms.ValidationError(
                "O e-mail é muito longo para ser utilizado como acesso."
            )

        if User.objects.filter(
            username__iexact=email
        ).exists() or User.objects.filter(
            email__iexact=email
        ).exists():
            raise forms.ValidationError(
                (
                    "Este e-mail já possui acesso cadastrado. "
                    "Utilize a página de entrada ou outro e-mail."
                )
            )

        return email

    def clean(self):

        cleaned_data = super().clean()

        tipo = cleaned_data.get(
            "tipo"
        )

        especialidade = cleaned_data.get(
            "especialidade"
        )

        categoria = cleaned_data.get(
            "categoria"
        )

        plano = cleaned_data.get(
            "plano"
        )

        senha = cleaned_data.get(
            "senha"
        )

        confirmar_senha = cleaned_data.get(
            "confirmar_senha"
        )

        if (
            tipo
            == SolicitacaoCadastro.TIPO_PROFISSIONAL
            and not especialidade
        ):

            self.add_error(
                "especialidade",
                "Informe a especialidade do profissional.",
            )

        if (
            tipo
            == SolicitacaoCadastro.TIPO_EMPRESA
            and not categoria
        ):

            self.add_error(
                "categoria",
                "Informe a categoria da empresa.",
            )

        if plano and not plano.ativo:

            self.add_error(
                "plano",
                "Este plano não está disponível.",
            )

        if senha and confirmar_senha and senha != confirmar_senha:

            self.add_error(
                "confirmar_senha",
                "As senhas informadas não são iguais.",
            )

        if senha:

            User = get_user_model()

            usuario_temporario = User(
                username=cleaned_data.get("email", ""),
                email=cleaned_data.get("email", ""),
            )

            try:
                validate_password(
                    senha,
                    user=usuario_temporario,
                )
            except ValidationError as erro:
                self.add_error(
                    "senha",
                    erro,
                )

        return cleaned_data
