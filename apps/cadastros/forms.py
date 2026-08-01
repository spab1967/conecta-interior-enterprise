from django import forms
from django.contrib.auth import get_user_model
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError

from apps.categorias.models import Categoria
from apps.cidades.models import Cidade
from apps.planos.models import Plano

from .models import SolicitacaoCadastro


ESPECIALIDADES_SERVICOS = (
    "Acompanhante de idosos",
    "Acompanhante hospitalar",
    "Açougueiro",
    "Acupunturista",
    "Adestrador de cães",
    "Advogado",
    "Afinador de instrumentos",
    "Agente de viagens",
    "Agrimensor",
    "Agrônomo",
    "Ajudante de carga e descarga",
    "Ajudante de cozinha",
    "Ajudante de obras",
    "Alfaiate",
    "Alinhador automotivo",
    "Analista de sistemas",
    "Animador de festas",
    "Antennista",
    "Apicultor",
    "Aplicador de películas",
    "Aplicador de sinteco",
    "Arquiteto",
    "Artesão",
    "Assistente administrativo",
    "Assistente de compras",
    "Assistente de informática",
    "Assistente virtual",
    "Atendente",
    "Ator",
    "Auditor",
    "Auxiliar de enfermagem",
    "Azulejista",
    "Babá",
    "Balanceador automotivo",
    "Banhista de animais",
    "Barbeiro",
    "Barman",
    "Bartender",
    "Biólogo",
    "Biomédico",
    "Bombeiro civil",
    "Bordadeira",
    "Borracheiro",
    "Buffet para eventos",
    "Cabeleireiro",
    "Cabeleireiro infantil",
    "Caldeireiro",
    "Calheiro",
    "Camareira",
    "Caminhoneiro",
    "Cantor",
    "Capinador",
    "Carpinteiro",
    "Carregador",
    "Cartazista",
    "Caseiro",
    "Ceramista",
    "Cerimonialista",
    "Chapeiro",
    "Chaveiro",
    "Chef de cozinha",
    "Chofer",
    "Churrasqueiro",
    "Cinegrafista",
    "Clínico de pés",
    "Coach",
    "Comprador profissional",
    "Comunicador visual",
    "Conciliador",
    "Confeiteiro",
    "Construtor",
    "Consultor ambiental",
    "Consultor contábil",
    "Consultor de alimentos",
    "Consultor de carreira",
    "Consultor de imagem",
    "Consultor de informática",
    "Consultor de marketing",
    "Consultor de moda",
    "Consultor de negócios",
    "Consultor de recursos humanos",
    "Consultor de segurança",
    "Consultor de vendas",
    "Consultor educacional",
    "Consultor financeiro",
    "Consultor jurídico",
    "Contador",
    "Controlador de pragas",
    "Copeira",
    "Corretor de imóveis",
    "Corretor de seguros",
    "Costureira",
    "Cozinheira",
    "Cuidador de animais",
    "Cuidador de crianças",
    "Cuidador de idosos",
    "Cuidador de pessoas com deficiência",
    "Decorador",
    "Dedetizador",
    "Desentupidor",
    "Designer de interiores",
    "Designer de moda",
    "Designer gráfico",
    "Despachante",
    "Digitador",
    "DJ",
    "Doméstica",
    "Eletricista automotivo",
    "Eletricista industrial",
    "Eletricista predial",
    "Eletricista rural",
    "Empregada doméstica",
    "Encanador",
    "Encanador industrial",
    "Enfermeiro",
    "Engenheiro agrônomo",
    "Engenheiro ambiental",
    "Engenheiro civil",
    "Engenheiro eletricista",
    "Engraxate",
    "Entregador",
    "Esteticista",
    "Estofador",
    "Farmacêutico",
    "Faxineira",
    "Ferramenteiro",
    "Filmagem de eventos",
    "Fisioterapeuta",
    "Fonoaudiólogo",
    "Fotógrafo",
    "Freteiro",
    "Funileiro",
    "Garagista",
    "Garçom",
    "Garçonete",
    "Geógrafo",
    "Geólogo",
    "Gesseiro",
    "Gestor de redes sociais",
    "Guia de turismo",
    "Guincheiro",
    "Impermeabilizador",
    "Instalador de alarmes",
    "Instalador de antenas",
    "Instalador de ar-condicionado",
    "Instalador de câmeras",
    "Instalador de cerca elétrica",
    "Instalador de cortinas",
    "Instalador de drywall",
    "Instalador de energia solar",
    "Instalador de esquadrias",
    "Instalador de forro",
    "Instalador de gás",
    "Instalador de granito",
    "Instalador de internet",
    "Instalador de papel de parede",
    "Instalador de piscinas",
    "Instalador de piso laminado",
    "Instalador de portão eletrônico",
    "Instalador de redes",
    "Instalador de som automotivo",
    "Instalador de toldos",
    "Instalador hidráulico",
    "Instrutor de academia",
    "Instrutor de dança",
    "Instrutor de informática",
    "Instrutor de música",
    "Intérprete",
    "Jardineiro",
    "Lanterneiro",
    "Lavadeira",
    "Lavador de carros",
    "Lavador de estofados",
    "Lavador de fachadas",
    "Lavador de tapetes",
    "Leiturista",
    "Limpador de caixa-d'água",
    "Limpador de calhas",
    "Limpador de piscina",
    "Limpador de terrenos",
    "Limpeza de ar-condicionado",
    "Limpeza de escritórios",
    "Limpeza de fachadas",
    "Limpeza de fossas",
    "Limpeza pós-obra",
    "Limpeza residencial",
    "Locutor",
    "Lubrificador",
    "Manicure",
    "Manutenção de celulares",
    "Manutenção de computadores",
    "Manutenção de impressoras",
    "Manutenção de jardins",
    "Manutenção de piscinas",
    "Manutenção predial",
    "Maquiador",
    "Marceneiro",
    "Marido de aluguel",
    "Marmoreiro",
    "Massagista",
    "Mecânico agrícola",
    "Mecânico de bicicletas",
    "Mecânico de máquinas",
    "Mecânico de motos",
    "Mecânico de veículos",
    "Mediador",
    "Mestre de cerimônias",
    "Mestre de obras",
    "Montador de andaimes",
    "Montador de estruturas",
    "Montador de móveis",
    "Motoboy",
    "Motorista",
    "Motorista de aplicativo",
    "Mototaxista",
    "Músico",
    "Nutricionista",
    "Oficineiro",
    "Operador de máquinas agrícolas",
    "Organizador de eventos",
    "Organizador profissional",
    "Padeiro",
    "Paisagista",
    "Panfleteiro",
    "Passadeira",
    "Pedagogo",
    "Pedicure",
    "Pedreiro",
    "Perito",
    "Personal organizer",
    "Personal trainer",
    "Pintor automotivo",
    "Pintor de móveis",
    "Pintor industrial",
    "Pintor predial",
    "Pizzaiolo",
    "Podador de árvores",
    "Professor de artes",
    "Professor de dança",
    "Professor de educação física",
    "Professor de idiomas",
    "Professor de informática",
    "Professor de música",
    "Professor de reforço escolar",
    "Professor particular",
    "Projetista",
    "Psicólogo",
    "Publicitário",
    "Recepcionista",
    "Recreador infantil",
    "Redator",
    "Relojoeiro",
    "Reparador de eletrodomésticos",
    "Reparador de ferramentas",
    "Reparador de móveis",
    "Representante comercial",
    "Revisor de textos",
    "Salgadeiro",
    "Sanfoneiro",
    "Sapateiro",
    "Secretária",
    "Segurança particular",
    "Serralheiro",
    "Servente de pedreiro",
    "Soldador",
    "Sommelier",
    "Sonoplasta",
    "Tapeceiro",
    "Tapeceiro automotivo",
    "Tatuador",
    "Técnico agrícola",
    "Técnico de celular",
    "Técnico de enfermagem",
    "Técnico de informática",
    "Técnico de refrigeração",
    "Técnico de segurança do trabalho",
    "Técnico de som",
    "Técnico em eletrônica",
    "Técnico em energia solar",
    "Técnico em manutenção industrial",
    "Técnico em redes",
    "Técnico em telefonia",
    "Terapeuta",
    "Topógrafo",
    "Tosador de animais",
    "Tradutor",
    "Transportador de cargas",
    "Tratorista",
    "Turismólogo",
    "Vaqueiro",
    "Veterinário",
    "Vidraceiro",
    "Vigia",
    "Web designer",
    "Zelador",
)


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
                    "list": "especialidades-servicos",
                    "autocomplete": "off",
                    "placeholder":
                        "Digite ou escolha uma profissão ou serviço",
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

        self.especialidades_servicos = ESPECIALIDADES_SERVICOS

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
