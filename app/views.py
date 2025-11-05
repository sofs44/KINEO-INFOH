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
    nome = forms.CharField(max_length=150, label="Nome de usuário")
    email = forms.EmailField(required=True, label="E-mail")
    senha = forms.CharField(widget=forms.PasswordInput, label="Senha")
    senha2 = forms.CharField(widget=forms.PasswordInput, label="Confirmar senha")
    idade = forms.DateField(required=False, widget=forms.DateInput(attrs={"type": "date"}))


class LoginForm(forms.Form):
    username = forms.CharField(label="Nome de usuário")
    senha = forms.CharField(widget=forms.PasswordInput, label="Senha")


class PreferenciaForm(forms.ModelForm):
    class Meta:
        model = Preferencia
        fields = ["esportes", "sexo", "nivel", "turno", "idade_parc"]


class ParceiroSearchForm(forms.Form):
    termo = forms.CharField(required=False, label="Nome ou esporte")
    localizacao = forms.CharField(required=False)
    esporte = forms.CharField(required=False)


class MensagemForm(forms.Form):
    destinatario_id = forms.IntegerField(widget=forms.HiddenInput, required=False) # Tornando opcional
    grupo_id = forms.IntegerField(widget=forms.HiddenInput, required=False) # Novo campo para grupo
    mensagem = forms.CharField(widget=forms.Textarea)


class GrupoForm(forms.ModelForm):
    class Meta:
        model = Grupo
        fields = ["nome", "descricao", "localizacao"]


class DesafioForm(forms.ModelForm):
    class Meta:
        model = Desafio
        fields = ["id_grupo", "titulo", "descricao", "data_inicio", "data_fim"]
        widgets = {
            "data_inicio": forms.DateInput(attrs={"type": "date"}),
            "data_fim": forms.DateInput(attrs={"type": "date"})
        }


# ======== Views de autenticação ========

def registrar_view(request):
    if request.method == "POST":
        form = RegisterForm(request.POST)
        if form.is_valid():
            nome = form.cleaned_data["nome"]
            email = form.cleaned_data["email"]
            senha = form.cleaned_data["senha"]
            senha2 = form.cleaned_data["senha2"]
            idade = form.cleaned_data.get("idade")

            # Verifica senhas
            if senha != senha2:
                form.add_error("senha2", "As senhas não coincidem.")
                return render(request, "registrar.html", {"form": form})

            # Verifica se nome já existe
            if Usuario.objects.filter(nome=nome).exists():
                form.add_error("nome", "Este nome de usuário já está em uso.")
                return render(request, "registrar.html", {"form": form})

            # Cria usuário corretamente
            user = Usuario.objects.create_user(nome=nome, password=senha, email=email)
            if idade:
                user.idade = idade
                user.save()

            # Faz login e redireciona
            auth_login(request, user)
            return redirect("home")
    else:
        form = RegisterForm()

    return render(request, "registrar.html", {"form": form})



def login_view(request):
    if request.method == "POST":
        form = LoginForm(request.POST)
        if form.is_valid():
            username = form.cleaned_data["username"]
            senha = form.cleaned_data["senha"]
            user = authenticate(request, username=username, password=senha)
            if user is not None:
                auth_login(request, user)
                return redirect("home")
            else:
                form.add_error(None, "Nome de usuário ou senha inválidos.")
    else:
        form = LoginForm()
    return render(request, "login.html", {"form": form})


def logout_view(request):
    auth_logout(request)
    return redirect("home")


# ======== Views principais ========

def home(request):
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
            return redirect("home")
    else:
        form = PreferenciaForm(instance=pref)
    return render(request, "editar_preferencia.html", {"form": form})


@login_required
def deletar_preferencia(request, pk):
    pref = get_object_or_404(Preferencia, pk=pk, usuario=request.user)
    if request.method == "POST":
        pref.delete()
        return redirect("home")
    return render(request, "confirm_delete.html", {"obj": pref})


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
                Q(usuario__username__icontains=termo) | Q(preferencia__esportes__icontains=termo)
            )
        if localizacao:
            parceiros = parceiros.filter(localizacao__icontains=localizacao)
        if esporte:
            parceiros = parceiros.filter(preferencia__esportes__icontains=esporte)
    return render(request, "buscar_parceiros.html", {"form": form, "parceiros": parceiros})


def visualizar_ranking(request):
    ranking_list = Ranking.objects.select_related("usuario").order_by("-pontuacao_total")[:50]
    return render(request, "ranking.html", {"ranking_list": ranking_list})


# =================================================================
# VIEWS DE CHAT (MODIFICADAS/ADICIONADAS)
# =================================================================

def chat_view(request):
    """
    View principal do chat. Exibe a lista de conversas (amigos e grupos)
    se o usuário estiver logado. Caso contrário, exibe a mensagem de login.
    """
    if not request.user.is_authenticated:
        # Renderiza a mensagem de não logado (que estará no template chat.html)
        return render(request, "chat.html", {"is_authenticated": False})

    # Lógica para usuários logados
    user = request.user
    
    # 1. Amigos (Assumindo que 'amigos' são usuários com quem o usuário logado já trocou mensagens)
    # Buscamos todos os usuários com quem o usuário logado já conversou
    contatos_ids = Mensagem.objects.filter(
        Q(id_remetente=user) | Q(id_destinatario=user)
    ).values_list('id_remetente__id_usuario', 'id_destinatario__id_usuario').distinct()
    
    # Flatten the list of IDs and remove the current user's ID
    all_ids = set()
    for sender_id, receiver_id in contatos_ids:
        all_ids.add(sender_id)
        all_ids.add(receiver_id)
    
    all_ids.discard(user.id_usuario)
    
    amigos = Usuario.objects.filter(id_usuario__in=all_ids).order_by('nome')

    # 2. Grupos
    grupos = user.grupos.all().order_by('nome')
    
    conversations = []
    
    # Adicionar Amigos
    for amigo in amigos:
        # Buscar a última mensagem trocada com este amigo
        last_message_obj = Mensagem.objects.filter(
            Q(id_remetente=user, id_destinatario=amigo) | Q(id_remetente=amigo, id_destinatario=user)
        ).order_by('-hora').first()
        
        last_message = last_message_obj.mensagem if last_message_obj else "Inicie a conversa"
        
        conversations.append({
            'id': amigo.id_usuario,
            'nome': amigo.nome,
            'foto_perfil': amigo.foto_perfil,
            'last_message': last_message,
            'is_group': False,
            'is_active': False, # Será definido na view de conversa específica
        })

    # Adicionar Grupos
    for grupo in grupos:
        # Como o modelo Mensagem não tem campo para Grupo, estou simulando a última mensagem
        # Você precisará de um modelo de Mensagem de Grupo para ter a última mensagem real
        conversations.append({
            'id': grupo.id_grupo,
            'nome': grupo.nome,
            'foto_perfil': None, # Grupos usam ícone
            'last_message': f"Membros: {grupo.membros.count()}", # Mensagem placeholder
            'is_group': True,
            'is_active': False,
        })
        
    context = {
        "is_authenticated": True,
        "conversations": conversations,
    }
    
    return render(request, "chat.html", context)


@login_required
def conversa(request, usuario_id):
    """
    View para exibir a conversa individual com outro usuário.
    """
    user = request.user
    contato = get_object_or_404(Usuario, id_usuario=usuario_id)
    
    # Verifica se o contato é o próprio usuário (evita chat consigo mesmo)
    if contato == user:
        return redirect('chat_view') # Ou uma página de erro

    # Mensagens entre o usuário logado e o contato
    mensagens = Mensagem.objects.filter(
        Q(id_remetente=user, id_destinatario=contato) | Q(id_remetente=contato, id_destinatario=user)
    ).order_by("hora")
    
    # Lógica de envio de mensagem
    if request.method == "POST":
        form = MensagemForm(request.POST)
        if form.is_valid():
            Mensagem.objects.create(
                id_remetente=user,
                id_destinatario=contato,
                mensagem=form.cleaned_data["mensagem"],
            )
            # Redireciona para evitar reenvio de formulário
            return redirect("conversa", usuario_id=contato.id_usuario)
    else:
        form = MensagemForm(initial={"destinatario_id": contato.id_usuario})
        
    # Reutiliza a lógica de lista de conversas da chat_view para a sidebar
    # (Isso deve ser otimizado, mas para o escopo atual, é funcional)
    
    contatos_ids = Mensagem.objects.filter(
        Q(id_remetente=user) | Q(id_destinatario=user)
    ).values_list('id_remetente__id_usuario', 'id_destinatario__id_usuario').distinct()
    
    all_ids = set()
    for sender_id, receiver_id in contatos_ids:
        all_ids.add(sender_id)
        all_ids.add(receiver_id)
    
    all_ids.discard(user.id_usuario)
    
    amigos = Usuario.objects.filter(id_usuario__in=all_ids).order_by('nome')
    grupos_list = user.grupos.all().order_by('nome')
    
    conversations = []
    
    for amigo in amigos:
        last_message_obj = Mensagem.objects.filter(
            Q(id_remetente=user, id_destinatario=amigo) | Q(id_remetente=amigo, id_destinatario=user)
        ).order_by('-hora').first()
        
        last_message = last_message_obj.mensagem if last_message_obj else "Inicie a conversa"
        
        conversations.append({
            'id': amigo.id_usuario,
            'nome': amigo.nome,
            'foto_perfil': amigo.foto_perfil,
            'last_message': last_message,
            'is_group': False,
            'is_active': amigo.id_usuario == usuario_id,
        })
        
    for grupo in grupos_list:
        conversations.append({
            'id': grupo.id_grupo,
            'nome': grupo.nome,
            'foto_perfil': None,
            'last_message': f"Membros: {grupo.membros.count()}",
            'is_group': True,
            'is_active': False,
        })


    context = {
        "is_authenticated": True,
        "conversations": conversations,
        "active_conversation": {
            'id': contato.id_usuario,
            'nome': contato.nome,
            'is_group': False,
        },
        "mensagens": mensagens,
        "form": form,
    }
    
    return render(request, "chat.html", context)


@login_required
def conversa_grupo(request, grupo_id):
    """
    View para exibir a conversa em grupo.
    """
    user = request.user
    grupo = get_object_or_404(Grupo, id_grupo=grupo_id)
    
    # Verifica se o usuário é membro do grupo
    if user not in grupo.membros.all():
        return HttpResponseForbidden("Você não é membro deste grupo.")

    # **NOTA:** Como o modelo Mensagem original não suporta grupos, 
    # esta parte é um placeholder. Você precisaria de um modelo como 'MensagemGrupo'.
    # Para fins de demonstração do layout, simulamos mensagens.
    # Se você adicionar um modelo 'MensagemGrupo', substitua o código abaixo.
    
    # Simulação de mensagens para demonstração do layout
    mensagens = [] # Lista vazia ou com mensagens simuladas
    
    # Lógica de envio de mensagem (adaptada para grupo)
    if request.method == "POST":
        form = MensagemForm(request.POST)
        if form.is_valid() and form.cleaned_data.get('grupo_id') == grupo.id_grupo:
            # **AQUI VOCÊ DEVE SALVAR A MENSAGEM NO SEU NOVO MODELO MensagemGrupo**
            # Exemplo: MensagemGrupo.objects.create(grupo=grupo, remetente=user, mensagem=form.cleaned_data["mensagem"])
            # Por enquanto, apenas redireciona
            return redirect("conversa_grupo", grupo_id=grupo.id_grupo)
    else:
        form = MensagemForm(initial={"grupo_id": grupo.id_grupo})
        
    # Reutiliza a lógica de lista de conversas da chat_view para a sidebar
    contatos_ids = Mensagem.objects.filter(
        Q(id_remetente=user) | Q(id_destinatario=user)
    ).values_list('id_remetente__id_usuario', 'id_destinatario__id_usuario').distinct()
    
    all_ids = set()
    for sender_id, receiver_id in contatos_ids:
        all_ids.add(sender_id)
        all_ids.add(receiver_id)
    
    all_ids.discard(user.id_usuario)
    
    amigos = Usuario.objects.filter(id_usuario__in=all_ids).order_by('nome')
    grupos_list = user.grupos.all().order_by('nome')
    
    conversations = []
    
    for amigo in amigos:
        last_message_obj = Mensagem.objects.filter(
            Q(id_remetente=user, id_destinatario=amigo) | Q(id_remetente=amigo, id_destinatario=user)
        ).order_by('-hora').first()
        
        last_message = last_message_obj.mensagem if last_message_obj else "Inicie a conversa"
        
        conversations.append({
            'id': amigo.id_usuario,
            'nome': amigo.nome,
            'foto_perfil': amigo.foto_perfil,
            'last_message': last_message,
            'is_group': False,
            'is_active': False,
        })
        
    for g in grupos_list:
        conversations.append({
            'id': g.id_grupo,
            'nome': g.nome,
            'foto_perfil': None,
            'last_message': f"Membros: {g.membros.count()}",
            'is_group': True,
            'is_active': g.id_grupo == grupo_id,
        })


    context = {
        "is_authenticated": True,
        "conversations": conversations,
        "active_conversation": {
            'id': grupo.id_grupo,
            'nome': grupo.nome,
            'is_group': True,
        },
        "mensagens": mensagens,
        "form": form,
    }
    
    return render(request, "chat.html", context)


@login_required
def enviar_mensagem(request, destinatario_id):
    destinatario = get_object_or_404(Usuario, id_usuario=destinatario_id)
    if request.method == "POST":
        form = MensagemForm(request.POST)
        if form.is_valid():
            Mensagem.objects.create(
                id_remetente=request.user,
                id_destinatario=destinatario,
                mensagem=form.cleaned_data["mensagem"],
            )
            return redirect("conversa", usuario_id=destinatario.id_usuario)
    else:
        form = MensagemForm(initial={"destinatario_id": destinatario_id})
    return render(request, "enviar_mensagem.html", {"form": form, "destinatario": destinatario})


# A view `conversa` original foi substituída pela nova versão acima.
# O restante das views (criar_grupo, listar_grupos, etc.) permanece inalterado.

@login_required
def criar_grupo(request):
    if request.method == "POST":
        form = GrupoForm(request.POST)
        if form.is_valid():
            grupo = form.save()
            grupo.membros.add(request.user)
            GrupoAdmin.objects.create(grupo=grupo, usuario=request.user)
            return redirect("ver_grupo", grupo_id=grupo.id_grupo)
    else:
        form = GrupoForm()
    return render(request, "criar_grupo.html", {"form": form})


def listar_grupos(request):
    qs = Grupo.objects.all()
    q = request.GET.get("q")
    if q:
        qs = qs.filter(Q(nome__icontains=q) | Q(localizacao__icontains=q) | Q(descricao__icontains=q))
    return render(request, "listar_grupos.html", {"grupos": qs})


def ver_grupo(request, grupo_id):
    grupo = get_object_or_404(Grupo, id_grupo=grupo_id)
    is_admin = request.user.is_authenticated and GrupoAdmin.objects.filter(grupo=grupo, usuario=request.user).exists()
    desafios = grupo.desafios.all()
    return render(request, "ver_grupo.html", {"grupo": grupo, "is_admin": is_admin, "desafios": desafios})


@login_required
def cadastrar_desafio(request):
    if request.method == "POST":
        form = DesafioForm(request.POST)
        if form.is_valid():
            desafio = form.save()
            return redirect("ver_grupo", grupo_id=desafio.id_grupo.id_grupo)
    else:
        form = DesafioForm()
        form.fields["id_grupo"].queryset = Grupo.objects.filter(admins__usuario=request.user)
    return render(request, "cadastrar_desafio.html", {"form": form})


@login_required
def marcar_conclusao(request, desafio_id):
    desafio = get_object_or_404(Desafio, id_desafio=desafio_id)
    if Conclusao.objects.filter(id_desafio=desafio, id_usuario=request.user).exists():
        return HttpResponse("Você já marcou este desafio como concluído")
    Conclusao.objects.create(id_desafio=desafio, id_usuario=request.user, data_conclusao=timezone.now().date())
    return redirect("ver_grupo", grupo_id=desafio.id_grupo.id_grupo)

def sobre(request):
    return render(request, 'sobre.html')

@login_required
def perfil_view(request):
    return render(request, 'perfil.html')


# view do perfil

@login_required
def perfil_view(request):
    """
    View para exibir e editar o perfil do usuário.
    """
    if request.method == "POST":
        # Processar edição de nome, email e foto
        nome = request.POST.get('nome')
        email = request.POST.get('email')
        foto = request.FILES.get('foto_perfil')
        
        user = request.user
        
        if nome:
            user.nome = nome
        if email:
            user.email = email
        if foto:
            user.foto_perfil = foto
        
        user.save()
        
        # Redirecionar ou renderizar com mensagem de sucesso
        return redirect('perfil')
    
    context = {
        'user': request.user,
    }
    return render(request, 'configuracoes.html', context)

# deletar conta 
@login_required
def deletar_conta_view(request):
    """
    View para deletar a conta do usuário.
    """
    if request.method == "POST":
        user = request.user
        user.delete()
        auth_logout(request)
        return redirect('home')
    
    return render(request, 'confirmar_delecao.html')