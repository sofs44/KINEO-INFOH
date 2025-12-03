from django.contrib import admin
from django.urls import path
from app import views
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    # Admin
    path('admin/', admin.site.urls),

    # Comunidades
    path("comunidades/", views.comunidades, name="comunidades"),
    path("criar-comunidade/", views.criar_comunidade, name="criar_comunidade"),
    path("comunidade/<int:comunidade_id>/metas/", views.metas_view, name="metas"),
    path("entrar_comunidade/<int:comunidade_id>/", views.entrar_comunidade, name="entrar_comunidade"),
    path("sair_comunidade/<int:comunidade_id>/", views.sair_comunidade, name="sair_comunidade"),
    path("comunidade/<int:comunidade_id>/adicionar_meta/", views.adicionar_meta, name="adicionar_meta"),
    path("comunidade/<int:comunidade_id>/criar_meta_ajax/", views.criar_meta_ajax, name="criar_meta_ajax"),
    path("ranking/", views.ranking_global, name="ranking_global"),
    path("meta/<int:meta_id>/cumprir/", views.cumprir_meta, name="cumprir_meta"),
    # Rotas gerais
    path("", views.home, name="home"), 
    path("sobre/", views.sobre, name="sobre"),
    path("registrar/", views.registrar_view, name="registrar"),
    path("login/", views.login_view, name="login"),
    path("logout/", views.logout_view, name="logout"),
    path("perfil/", views.perfil_view, name="perfil"),
    path("deletar-conta/", views.deletar_conta_view, name="deletar_conta"),
    path("buscar_parceiros/", views.buscar_parceiros, name="buscar_parceiros"),

    # Preferências
    path("preferencia/editar/", views.editar_preferencia, name="editar_preferencia"),
    path("preferencia/deletar/<int:pk>/", views.deletar_preferencia, name="deletar_preferencia"),

    # Ranking global (sem comunidade)
    # Mensagens e conversas
    path("mensagem/enviar/<int:destinatario_id>/", views.enviar_mensagem, name="enviar_mensagem"),
    path("conversa/<int:usuario_id>/", views.conversa, name="conversa"),

    # Grupos
    path("grupos/", views.listar_grupos, name="listar_grupos"),
    path("grupo/<int:grupo_id>/", views.ver_grupo, name="ver_grupo"),
    path("grupo/criar/", views.criar_grupo, name="criar_grupo"),

    # Desafios
    path("desafio/cadastrar/", views.cadastrar_desafio, name="cadastrar_desafio"),
    path("desafio/mark/<int:desafio_id>/", views.marcar_conclusao, name="marcar_conclusao"),

    # Chat
    path("chat/", views.chat_view, name="chat"),
    path("chat/u/<int:usuario_id>/", views.conversa, name="conversa"),  # Conversa individual
    path("chat/g/<int:grupo_id>/", views.conversa_grupo, name="conversa_grupo"),  # Conversa em grupo
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
