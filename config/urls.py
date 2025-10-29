from django.contrib import admin
from django.urls import path, include
from app import views
from django.conf import settings
from django.conf.urls.static import static

app_name = "kineo"

urlpatterns = [
    # Admin
    path('admin/', admin.site.urls),

    # Rotas do seu app
    path("", views.home, name="home"), 
    path('sobre/', views.sobre, name='sobre'),
    path("registrar/", views.registrar_view, name="registrar"),
    path("login/", views.login_view, name="login"),
    path("chat/", views.chat_view, name="chat"),
    path('logout/', views.logout_view, name='logout'),
    path('perfil/', views.perfil_view, name='perfil'),
    path("preferencia/editar/<int:pk>/", views.editar_preferencia, name="editar_preferencia"),
    path("preferencia/novo/", views.editar_preferencia, name="nova_preferencia"),
    path("preferencia/deletar/<int:pk>/", views.deletar_preferencia, name="deletar_preferencia"),
    path("buscar_parceiros/", views.buscar_parceiros, name="buscar_parceiros"),
    path("ranking/", views.visualizar_ranking, name="ranking"),
    path("mensagem/enviar/<int:destinatario_id>/", views.enviar_mensagem, name="enviar_mensagem"),
    path("conversa/<int:usuario_id>/", views.conversa, name="conversa"),
    path("grupos/", views.listar_grupos, name="listar_grupos"),
    path("grupo/<int:grupo_id>/", views.ver_grupo, name="ver_grupo"),
    path("grupo/criar/", views.criar_grupo, name="criar_grupo"),
    path("desafio/cadastrar/", views.cadastrar_desafio, name="cadastrar_desafio"),
    path("desafio/mark/<int:desafio_id>/", views.marcar_conclusao, name="marcar_conclusao"),
    path('chat/', views.chat_view, name='chat_view'),
    path('chat/u/<int:usuario_id>/', views.conversa, name='conversa'), # Conversa individual
    path('chat/g/<int:grupo_id>/', views.conversa_grupo, name='conversa_grupo'), # Conversa em grupo
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)