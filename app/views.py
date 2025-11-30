from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login as auth_login, logout as auth_logout
from django.contrib.auth.decorators import login_required
from django.urls import reverse
from django.http import HttpResponse, HttpResponseForbidden, JsonResponse, HttpResponseBadRequest
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
from .models import Comunidade, MetaComunidade
from django.views.decorators.csrf import csrf_exempt
from django.http import JsonResponse
import json
from django.db import ProgrammingError



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
        # AQUI HÁ UM PONTO DE MELHORIA:
        # Se um usuário puder ter VÁRIAS preferências, .all() está correto.
        # Se ele só puder ter UMA, o ideal é usar .first()
        context["preferencias"] = request.user.preferencias.all() 
        context["grupos"] = request.user.grupos.all()
    return render(request, "home.html", context)


# =================================================================
# CORREÇÃO 1: View editar_preferencia
# =================================================================
# Em views.py, substitua sua função 'editar_preferencia' por esta:

@login_required
def editar_preferencia(request):
    
    print("\n--- REQUISIÇÃO 'editar_preferencia' RECEBIDA ---")

    try:
        # 1. Buscamos a preferência que o usuário JÁ TEM.
        pref_instance = request.user.preferencias.first()
        print(f"1. Instância de preferência encontrada: {pref_instance}")

        if request.method == "POST":
            print("2. Método é POST. Processando formulário...")
            
            form = PreferenciaForm(request.POST, instance=pref_instance)
            
            if form.is_valid():
                print("3. Formulário é VÁLIDO.")
                pref = form.save(commit=False)
                pref.usuario = request.user  # Garante a associação correta
                
                print("4. Prestes a salvar no banco de dados...")
                pref.save()
                print("5. SALVO COM SUCESSO!")
                
                return JsonResponse({"success": True})
            else:
                # Se o formulário for inválido, não é um 500, mas é bom sabermos
                print(f"3. Formulário é INVÁLIDO. Erros: {form.errors.as_json()}")
                return JsonResponse({"success": False, "errors": form.errors})
        
        # Se não for POST (ex: GET), o que não deveria acontecer pelo JS
        print("2. Método NÃO é POST. Requisição inválida.")
        return HttpResponseBadRequest("Requisição inválida (só POST é permitido)")

    except Exception as e:
        # 6. Se QUALQUER coisa quebrar, vai cair aqui!
        print(f"!!! ERRO 500 CAPTURADO !!!\nTipo: {type(e)}\nErro: {e}")
        # Retorna um JSON de erro em vez de quebrar
        return JsonResponse({"success": False, "error": str(e)}, status=500)

@login_required
def deletar_preferencia(request, pk):
    pref = get_object_or_404(Preferencia, pk=pk, usuario=request.user)
    if request.method == "POST":
        pref.delete()
        return redirect("home")
    return render(request, "confirm_delete.html", {"obj": pref})


from django.contrib.auth.decorators import login_required
from django.db.models import Q
from datetime import date

# --- Helpers de apresentação ---
def calcular_idade(data_nascimento):
    if not data_nascimento:
        return None
    hoje = date.today()
    return hoje.year - data_nascimento.year - (
        (hoje.month, hoje.day) < (data_nascimento.month, data_nascimento.day)
    )

def get_profile_color(usuario):
    """
    Placeholder para futura personalização de cor pelo usuário.
    Quando você criar o campo, é só substituir aqui.
    """
    return "#ff9800"  # Laranja padrão

def montar_descricao(parceiro):
    pref = parceiro.preferencia
    esporte = (pref.esportes if pref and pref.esportes else "Não informado")
    nivel = (pref.get_nivel_display() if pref and pref.nivel else "Não informado")
    idade_calc = calcular_idade(parceiro.usuario.idade)
    idade_txt = f"{idade_calc} anos" if idade_calc is not None else "Não informada"
    local = parceiro.localizacao if parceiro.localizacao else "Não informada"
    return f"Esporte: {esporte} | Idade: {idade_txt} | Nível: {nivel} | Localização: {local}"

@login_required
def buscar_parceiros(request):
    # 1. Captura os dados direto da URL (barra de pesquisa)
    termo = request.GET.get('termo')
    esporte = request.GET.get('esporte')
    localizacao = request.GET.get('localizacao')

    # 2. Começa pegando TODOS os usuários, menos o próprio usuário logado
    # O prefetch_related deixa o carregamento mais rápido (otimização)
    users = Usuario.objects.exclude(id_usuario=request.user.id_usuario).prefetch_related('preferencias', 'parceiros')

    # 3. Aplica o filtro de pesquisa (Nome OU Esporte)
    if termo:
        users = users.filter(
            Q(nome__icontains=termo) | 
            Q(preferencias__esportes__icontains=termo)
        ).distinct()

    # 4. Aplica filtro específico de Esporte (do Modal)
    if esporte:
        users = users.filter(preferencias__esportes__icontains=esporte).distinct()

    # 5. Aplica filtro específico de Localização (do Modal)
    if localizacao:
        users = users.filter(parceiros__localizacao__icontains=localizacao).distinct()

    # 6. Envia para o HTML
    context = {
        'parceiros': users,
        'request': request # Necessário para manter o texto na barra de busca
    }

    return render(request, "buscar_parceiros.html", context)
    # Monta dados de apresentação
    parceiros = []
    for p in qs:
        parceiros.append({
            "nome": p.usuario.nome,
            "foto_url": p.usuario.foto_perfil.url if p.usuario.foto_perfil else None,
            "cor_avatar": get_profile_color(p.usuario),
            "descricao": montar_descricao(p),
        })

    # Exibe mensagem amigável quando não houver resultados
    sem_resultados = (len(parceiros) == 0)
    return render(
        request,
        "buscar_parceiros.html",
        {"form": form, "parceiros": parceiros, "sem_resultados": sem_resultados}
    )
def visualizar_ranking(request, comunidade_id):
    comunidade = get_object_or_404(Comunidade, id=comunidade_id)

    ranking_list = Ranking.objects.filter(
        usuario__comunidades__id=comunidade.id  # ou outro campo que relacione usuário à comunidade
    ).select_related("usuario").order_by("-pontuacao_total")[:50]

    return render(request, "ranking.html", {
        "ranking_list": ranking_list,
        "comunidade": comunidade,
        "user": request.user
    })


def chat_view(request):

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

# =================================================================
# CORREÇÃO 2: View perfil_view
# =================================================================

# Sua view original estava duplicada (linhas 503 e 514). Estou usando a versão da linha 514
# e corrigindo-a para enviar os dados da preferência para o template.

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
    
    # --- INÍCIO DA CORREÇÃO ---
    
    # 1. Buscamos a preferência ÚNICA do usuário
    #    Assumindo que um usuário só tem UMA preferência
    preferencia = request.user.preferencias.first()
    
    # 2. Criamos uma instância do formulário com os dados da preferência
    #    Isso vai pré-popular o modal de "Editar Preferências"
    pref_form = PreferenciaForm(instance=preferencia)

    context = {
        'user': request.user,
        'preferencia': preferencia,  # Enviamos o OBJETO para exibir na tela
        'pref_form': pref_form,      # Enviamos o FORM para o modal
    }
    return render(request, 'perfil.html', context)
    # --- FIM DA CORREÇÃO ---

# =================================================================


# deletar conta 
@login_required
def deletar_conta_view(request):
    if request.method == "POST":
        user = request.user
        user.delete()
        auth_logout(request)
        return redirect('home')
    
    return render(request, 'confirmar_delecao.html')

def comunidades(request):
    comunidades = Comunidade.objects.all()
    return render(request, "comunidades.html", {"comunidades": comunidades})

def entrar_comunidade(request, comunidade_id):
    comunidade = get_object_or_404(Comunidade, id=comunidade_id)

    if request.user not in comunidade.membros.all():
        comunidade.membros.add(request.user)

    # redireciona para a página de metas da comunidade
    return redirect('metas', comunidade_id=comunidade.id)

@csrf_exempt
def criar_comunidade(request):
    if request.method == "POST":
        data = json.loads(request.body)

        nome = data.get("nome")
        cor = data.get("cor")

        if not nome:
            return JsonResponse({"status": "erro", "msg": "Nome obrigatório"})

        Comunidade.objects.create(
            nome=nome,
            cor=cor,
            admin=request.user
        )

        return JsonResponse({"status": "ok"})

from django.db import ProgrammingError
from datetime import timedelta

def formatar_tempo(td: timedelta):
    dias = td.days
    horas, resto = divmod(td.seconds, 3600)
    minutos, segundos = divmod(resto, 60)
    # Se não tiver dias, usa apenas HH:MM:SS
    if dias and dias > 0:
        return f"{dias} {horas:02}:{minutos:02}:{segundos:02}"
    return f"{horas:02}:{minutos:02}:{segundos:02}"

def cor_escura(hex_cor: str) -> bool:
    hex_cor = (hex_cor or "").lstrip('#')
    if len(hex_cor) != 6:
        return False  # fallback: trata como claro
    r, g, b = (int(hex_cor[i:i+2], 16) for i in (0, 2, 4))
    luminancia = 0.299 * r + 0.587 * g + 0.114 * b
    return luminancia < 128

from django.shortcuts import render, get_object_or_404
from django.utils import timezone
from app.models import Comunidade, MetaComunidade, Ranking

from django.shortcuts import render, get_object_or_404
from django.utils import timezone
from app.models import Comunidade, MetaComunidade, Ranking

from django.shortcuts import render, get_object_or_404
from django.utils import timezone
from app.models import Comunidade, MetaComunidade, Ranking

def metas_view(request, comunidade_id):
    comunidade = get_object_or_404(Comunidade, id=comunidade_id)
    metas = MetaComunidade.objects.filter(comunidade=comunidade)

    # Pontos por metas cumpridas
    pontos = {}
    for meta in metas:
        for usuario in meta.usuarios_cumpriram.all():
            pontos[usuario] = pontos.get(usuario, 0) + 1

    # Atualiza ranking
    for usuario, score in pontos.items():
        ranking_obj, _ = Ranking.objects.get_or_create(usuario=usuario)
        ranking_obj.pontuacao_total = score
        ranking_obj.save()

    # Colocação do usuário
    colocacao = None
    if request.user.is_authenticated:
        ranking_ordenado = sorted(pontos.items(), key=lambda x: x[1], reverse=True)
        for i, (usuario, score) in enumerate(ranking_ordenado, start=1):
            if usuario == request.user:
                colocacao = i
                break

    # Tempo restante (aceita deadline DateTimeField ou DurationField somado ao criado_em)
    now = timezone.now()
    for meta in metas:
        deadline = None
        # Dentro do loop de metas:
        deadline = meta.criado_em + meta.tempo_limite
        delta = deadline - timezone.now()
        total = int(delta.total_seconds())
        meta.tempo_limite_formatado = f"{total // 3600} h {(total % 3600) // 60} m {total 

        # prazo_final: DateTimeField (se existir)
        if hasattr(meta, "prazo_final") and getattr(meta, "prazo_final"):
            deadline = meta.prazo_final
            if timezone.is_naive(deadline):
                deadline = timezone.make_aware(deadline, timezone.get_current_timezone())

        # tempo_limite: DurationField (se existir)
        elif hasattr(meta, "tempo_limite") and getattr(meta, "tempo_limite"):
            criado = meta.criado_em
            if timezone.is_naive(criado):
                criado = timezone.make_aware(criado, timezone.get_current_timezone())
            deadline = criado + meta.tempo_limite

        # Formatação
        if deadline:
            delta = deadline - now
            total = int(delta.total_seconds())
            if total <= 0:
                meta.tempo_limite_formatado = "0 h 0 m 0 s"
            else:
                h = total // 3600
                m = (total % 3600) // 60
                s = total % 60
                meta.tempo_limite_formatado = f"{h} h {m} m {s} s"
        else:
            meta.tempo_limite_formatado = "Sem limite"

        # Já cumpriu?
        meta.foi_cumprida_pelo_usuario = (
            request.user.is_authenticated and
            meta.usuarios_cumpriram.filter(pk=request.user.pk).exists()
        )

    context = {
        "comunidade": comunidade,
        "metas": metas,
        "colocacao": colocacao,
        "ranking_list": Ranking.objects.select_related("usuario").order_by("-pontuacao_total"),
        "sem_metas": not metas.exists(),
        "is_admin": request.user.is_authenticated and request.user == comunidade.admin,
    }
    return render(request, "metas.html", context)





def visualizar_ranking_global(request):
    ranking_list = Ranking.objects.select_related("usuario").order_by("-pontuacao_total")[:50]
    return render(request, "ranking.html", {"ranking_list": ranking_list, "user": request.user})


@login_required
def sair_comunidade(request, comunidade_id):
    comunidade = get_object_or_404(Comunidade, id=comunidade_id)

    if request.method == "POST":
        comunidade.membros.remove(request.user)
        return redirect("comunidades")  # volta para a lista de comunidades

    # Se alguém acessar via GET, só redireciona
    return redirect("comunidades")

@login_required
def cumprir_meta(request, meta_id):
    meta = get_object_or_404(MetaComunidade, id=meta_id)

    if request.method == "POST":
        meta.usuarios_cumpriram.add(request.user)
        return redirect("metas", comunidade_id=meta.comunidade.id)

    return redirect("metas", comunidade_id=meta.comunidade.id)


class MetaForm(forms.ModelForm):
    class Meta:
        model = MetaComunidade
        fields = ['titulo', 'tempo_limite']
        widgets = {
            'tempo_limite': forms.TextInput(attrs={'placeholder': 'Ex: 3 days, 2:00:00'}),
        }

@login_required
def adicionar_meta(request, comunidade_id):
    comunidade = get_object_or_404(Comunidade, id=comunidade_id)

    if request.user != comunidade.admin:
        return HttpResponseForbidden("Você não tem permissão para adicionar metas.")

    if request.method == "POST":
        form = MetaForm(request.POST)
        if form.is_valid():
            meta = form.save(commit=False)
            meta.comunidade = comunidade
            meta.save()
            return redirect('metas', comunidade_id=comunidade.id)
    else:
        form = MetaForm()

    return render(request, 'adicionar_meta.html', {'form': form, 'comunidade': comunidade})

@csrf_exempt
@login_required
def criar_meta_ajax(request, comunidade_id):
    comunidade = get_object_or_404(Comunidade, id=comunidade_id)

    if request.user != comunidade.admin:
        return JsonResponse({"status": "erro", "msg": "Sem permissão"})

    if request.method == "POST":
        titulo = request.POST.get("titulo")
        tempo_raw = request.POST.get("tempo_limite")

        try:
            tempo_limite = eval(f"datetime.timedelta({tempo_raw})")
        except:
            return JsonResponse({"status": "erro", "msg": "Formato de tempo inválido"})

        MetaComunidade.objects.create(
            comunidade=comunidade,
            titulo=titulo,
            tempo_limite=tempo_limite
        )

        return JsonResponse({"status": "ok"})

    return JsonResponse({"status": "erro", "msg": "Método inválido"})

@login_required
def sair_comunidade(request, comunidade_id):
    comunidade = get_object_or_404(Comunidade, id=comunidade_id)

    if request.method == "POST":
        comunidade.membros.remove(request.user)
        return redirect("comunidades")

    return redirect("comunidades")

def parse_tempo_limite(texto):
    """
    Converte 'HH:MM:SS' ou 'DD HH:MM:SS' em timedelta.
    Exemplos:
      - '02:30:00' -> 2h30m
      - '3 01:00:00' -> 3 dias e 1 hora
    """
    try:
        partes = texto.strip().split()
        if len(partes) == 1:
            # HH:MM:SS
            h, m, s = map(int, partes[0].split(":"))
            return datetime.timedelta(hours=h, minutes=m, seconds=s)
        elif len(partes) == 2:
            # DD HH:MM:SS
            d = int(partes[0])
            h, m, s = map(int, partes[1].split(":"))
            return datetime.timedelta(days=d, hours=h, minutes=m, seconds=s)
        else:
            return None
    except Exception:
        return None

@login_required
def criar_meta_ajax(request, comunidade_id):
    comunidade = get_object_or_404(Comunidade, id=comunidade_id)

    if request.user != comunidade.admin:
        return JsonResponse({"status": "erro", "msg": "Sem permissão"}, status=403)

    if request.method == "POST":
        titulo = request.POST.get("titulo", "").strip()
        tempo_raw = request.POST.get("tempo_limite", "").strip()

        if not titulo:
            return JsonResponse({"status": "erro", "msg": "Título é obrigatório"}, status=400)

        td = parse_tempo_limite(tempo_raw)
        if td is None:
            return JsonResponse({"status": "erro", "msg": "Formato de tempo inválido. Use HH:MM:SS ou DD HH:MM:SS"}, status=400)

        MetaComunidade.objects.create(
            comunidade=comunidade,
            titulo=titulo,
            tempo_limite=td
        )

        return JsonResponse({"status": "ok"})

    return JsonResponse({"status": "erro", "msg": "Método inválido"}, status=405)

