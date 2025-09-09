from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login as auth_login, logout as auth_logout
from django.contrib.auth.decorators import login_required
from django.urls import reverse
from django.http import HttpResponse, HttpResponseForbidden
from django import forms
from .models import (
    Usuario,
    Preferencia,
    Parceiro,
    Ranking,
    Mensagem,
    Grupo,
    GrupoAdmin,
    Desafio,
    Conclusao,
)
from django.db.models import Q
from django.utils import timezone


# ======== Forms simples usados pelas views ========
class RegisterForm(forms.Form):
    nome = forms.CharField(max_length=150)
    email = forms.EmailField()
    senha = forms.CharField(widget=forms.PasswordInput)
    idade = forms.DateField(required=False, widget=forms.DateInput(attrs={"type": "date"}))


class LoginForm(forms.Form):
    email = forms.EmailField()
    senha = forms.CharField(widget=forms.PasswordInput)


class PreferenciaForm(forms.ModelForm):
    class Meta:
        model = Preferencia
        fields = ["esportes", "sexo", "nivel", "turno", "idade_parc"]


class ParceiroSearchForm(forms.Form):
    termo = forms.CharField(required=False, label="Nome ou esporte")
    localizacao = forms.CharField(required=False)
    esporte = forms.CharField(required=False)


class MensagemForm(forms.Form):
    destinatario_id = forms.IntegerField(widget=forms.HiddenInput)
    mensagem = forms.CharField(widget=forms.Textarea)


class GrupoForm(forms.ModelForm):
    class Meta:
        model = Grupo
        fields = ["nome", "descricao", "localizacao"]


class DesafioForm(forms.ModelForm):
    class Meta:
        model = Desafio
        fields = ["id_grupo", "titulo", "descricao", "data_inicio", "data_fim"]
        widgets = {"data_inicio": forms.DateInput(attrs={"type": "date"}), "data_fim": forms.DateInput(attrs={"type": "date"})}


# ======== Views de autenticação ========
def register(request):
    if request.method == "POST":
        form = RegisterForm(request.POST)
        if form.is_valid():
            nome = form.cleaned_data["nome"]
            email = form.cleaned_data["email"]
            senha = form.cleaned_data["senha"]
            idade = form.cleaned_data.get("idade")
            if Usuario.objects.filter(email=email).exists():
                form.add_error("email", "Email já cadastrado")
            else:
                user = Usuario.objects.create_user(email=email, nome=nome, password=senha)
                if idade:
                    user.idade = idade
                    user.save()
                auth_login(request, user)
                return redirect("kineo:home")
    else:
        form = RegisterForm()
    return render(request, "kineo/register.html", {"form": form})


def login_view(request):
    if request.method == "POST":
        form = LoginForm(request.POST)
        if form.is_valid():
            email = form.cleaned_data["email"]
            senha = form.cleaned_data["senha"]
            user = authenticate(request, email=email, password=senha)
            if user is not None:
                auth_login(request, user)
                return redirect("kineo:home")
            else:
                form.add_error(None, "Credenciais inválidas")
    else:
        form = LoginForm()
    return render(request, "kineo/login.html", {"form": form})


def logout_view(request):
    auth_logout(request)
    return redirect("kineo:home")


# ======== Views principais ========
def home(request):
    # página inicial simples: se estiver logado, mostrar preferências e grupos.
    context = {}
    if request.user.is_authenticated:
        context["preferencias"] = request.user.preferencias.all()
        context["grupos"] = request.user.grupos.all()
    return render(request, "home.html", context)


@login_required
def editar_preferencia(request, pk=None):
    if pk:
        pref = get_object_or_404(Preferencia, pk=pk, usuario=request.user)
    else:
        pref = Preferencia(usuario=request.user)
    if request.method == "POST":
        form = PreferenciaForm(request.POST, instance=pref)
        if form.is_valid():
            pref = form.save(commit=False)
            pref.usuario = request.user
            pref.save()
            return redirect("kineo:home")
    else:
        form = PreferenciaForm(instance=pref)
    return render(request, "kineo/editar_preferencia.html", {"form": form})


@login_required
def deletar_preferencia(request, pk):
    pref = get_object_or_404(Preferencia, pk=pk, usuario=request.user)
    if request.method == "POST":
        pref.delete()
        return redirect("kineo:home")
    return render(request, "kineo/confirm_delete.html", {"obj": pref})


@login_required
def buscar_parceiros(request):
    form = ParceiroSearchForm(request.GET or None)
    parceiros = Parceiro.objects.select_related("usuario", "preferencia").all()
    if form.is_valid():
        termo = form.cleaned_data.get("termo")
        localizacao = form.cleaned_data.get("localizacao")
        esporte = form.cleaned_data.get("esporte")
        if termo:
            parceiros = parceiros.filter(
                Q(usuario__nome__icontains=termo) | Q(preferencia__esportes__icontains=termo)
            )
        if localizacao:
            parceiros = parceiros.filter(localizacao__icontains=localizacao)
        if esporte:
            parceiros = parceiros.filter(preferencia__esportes__icontains=esporte)
    return render(request, "kineo/buscar_parceiros.html", {"form": form, "parceiros": parceiros})


@login_required
def visualizar_ranking(request):
    rankings = Ranking.objects.select_related("usuario").order_by("-pontuacao_total")
    return render(request, "kineo/ranking.html", {"rankings": rankings})


@login_required
def enviar_mensagem(request, destinatario_id):
    destinatario = get_object_or_404(Usuario, id_usuario=destinatario_id)
    if request.method == "POST":
        form = MensagemForm(request.POST)
        if form.is_valid():
            mensagem = Mensagem.objects.create(
                id_remetente=request.user,
                id_destinatario=destinatario,
                mensagem=form.cleaned_data["mensagem"],
            )
            return redirect("kineo:conversa", usuario_id=destinatario.id_usuario)
    else:
        form = MensagemForm(initial={"destinatario_id": destinatario_id})
    return render(request, "kineo/enviar_mensagem.html", {"form": form, "destinatario": destinatario})


@login_required
def conversa(request, usuario_id):
    contato = get_object_or_404(Usuario, id_usuario=usuario_id)
    mensagens = Mensagem.objects.filter(
        Q(id_remetente=request.user, id_destinatario=contato) | Q(id_remetente=contato, id_destinatario=request.user)
    ).order_by("hora")
    form = MensagemForm(initial={"destinatario_id": contato.id_usuario})
    return render(request, "kineo/conversa.html", {"contato": contato, "mensagens": mensagens, "form": form})


# ======== Grupos e desafios ========
@login_required
def criar_grupo(request):
    if request.method == "POST":
        form = GrupoForm(request.POST)
        if form.is_valid():
            grupo = form.save()
            grupo.membros.add(request.user)
            GrupoAdmin.objects.create(grupo=grupo, usuario=request.user)
            return redirect("kineo:ver_grupo", grupo_id=grupo.id_grupo)
    else:
        form = GrupoForm()
    return render(request, "kineo/criar_grupo.html", {"form": form})


def listar_grupos(request):
    qs = Grupo.objects.all()
    q = request.GET.get("q")
    if q:
        qs = qs.filter(Q(nome__icontains=q) | Q(localizacao__icontains=q) | Q(descricao__icontains=q))
    return render(request, "kineo/listar_grupos.html", {"grupos": qs})


def ver_grupo(request, grupo_id):
    grupo = get_object_or_404(Grupo, id_grupo=grupo_id)
    is_admin = request.user.is_authenticated and GrupoAdmin.objects.filter(grupo=grupo, usuario=request.user).exists()
    desafios = grupo.desafios.all()
    return render(request, "kineo/ver_grupo.html", {"grupo": grupo, "is_admin": is_admin, "desafios": desafios})


@login_required
def cadastrar_desafio(request):
    # apenas admins de grupo podem criar desafios
    if request.method == "POST":
        form = DesafioForm(request.POST)
        if form.is_valid():
            desafio = form.save()
            return redirect("kineo:ver_grupo", grupo_id=desafio.id_grupo.id_grupo)
    else:
        form = DesafioForm()
        # restringir escolhas para grupos em que o usuário é admin
        form.fields["id_grupo"].queryset = Grupo.objects.filter(admins__usuario=request.user)
    return render(request, "kineo/cadastrar_desafio.html", {"form": form})


@login_required
def marcar_conclusao(request, desafio_id):
    desafio = get_object_or_404(Desafio, id_desafio=desafio_id)
    if Conclusao.objects.filter(id_desafio=desafio, id_usuario=request.user).exists():
        return HttpResponse("Você já marcou este desafio como concluído")
    Conclusao.objects.create(id_desafio=desafio, id_usuario=request.user, data_conclusao=timezone.now().date())
    return redirect("kineo:ver_grupo", grupo_id=desafio.id_grupo.id_grupo)
