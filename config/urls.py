from django.urls import path
from app import views

app_name = "kineo"

urlpatterns = [
    path("", views.home, name="home"),
    path("register/", views.register, name="register"),
    path("login/", views.login_view, name="login"),
    path("logout/", views.logout_view, name="logout"),
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
]
