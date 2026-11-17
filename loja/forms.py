from django.contrib.auth.forms import UserCreationForm


class CadastroForm(UserCreationForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        textos = {
            "username": ("Usuário", "Seu usuário"),
            "password1": ("Senha", "Crie uma senha"),
            "password2": ("Confirmar senha", "Repita a senha"),
        }
        for nome, campo in self.fields.items():
            rotulo, dica = textos[nome]
            campo.label = rotulo
            campo.help_text = ""          # remove os textos longos
            campo.widget.attrs.update({"class": "form-control", "placeholder": dica})