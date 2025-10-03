from django import forms
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from .models import Usuario

# Formulário de registro
class UsuarioRegisterForm(UserCreationForm):
    class Meta:
        model = Usuario
        fields = ['nome', 'email', 'password1', 'password2']


# Formulário de login
class UsuarioLoginForm(AuthenticationForm):
    username = forms.CharField(label="Nome de usuário")
    password = forms.CharField(widget=forms.PasswordInput)
