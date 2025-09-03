from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.utils.translation import gettext_lazy as _
from .models import (
    Usuario,
    Preferencia,
    Parceiro,
    Ranking,
    Mensagem,
    Desafio,
    Conclusao,
    Grupo,
    GrupoAdmin,
)


class UsuarioAdmin(BaseUserAdmin):
    ordering = ("email",)
    list_display = ("email", "nome", "is_staff", "is_superuser")
    fieldsets = (
        (None, {"fields": ("email", "password")}),
        (_("Informações pessoais"), {"fields": ("nome", "idade")}),
        (_("Permissões"), {"fields": ("is_active", "is_staff", "is_superuser", "groups", "user_permissions")}),
        (_("Datas"), {"fields": ("last_login", "date_joined")}),
    )
    add_fieldsets = (
        (
            None,
            {
                "classes": ("wide",),
                "fields": ("email", "nome", "password1", "password2"),
            },
        ),
    )
    search_fields = ("email", "nome")
    filter_horizontal = ("groups", "user_permissions")


@admin.register(Preferencia)
class PreferenciaAdmin(admin.ModelAdmin):
    list_display = ("id_preferencia", "usuario", "esportes", "nivel", "turno")
    search_fields = ("usuario__nome", "esportes")


@admin.register(Parceiro)
class ParceiroAdmin(admin.ModelAdmin):
    list_display = ("id_parceiros", "usuario", "localizacao")
    search_fields = ("usuario__nome", "localizacao")


@admin.register(Ranking)
class RankingAdmin(admin.ModelAdmin):
    list_display = ("id_ranking", "usuario", "pontuacao_total", "esporte_prat")
    search_fields = ("usuario__nome",)


@admin.register(Mensagem)
class MensagemAdmin(admin.ModelAdmin):
    list_display = ("id_mensagem", "id_remetente", "id_destinatario", "hora")
    search_fields = ("id_remetente__nome", "id_destinatario__nome", "mensagem")


@admin.register(Grupo)
class GrupoAdminAdmin(admin.ModelAdmin):
    list_display = ("id_grupo", "nome", "localizacao", "criado_em")
    search_fields = ("nome", "localizacao")


@admin.register(GrupoAdmin)
class GrupoAdminInline(admin.ModelAdmin):
    list_display = ("id", "grupo", "usuario")
    search_fields = ("grupo__nome", "usuario__nome")


@admin.register(Desafio)
class DesafioAdmin(admin.ModelAdmin):
    list_display = ("id_desafio", "titulo", "id_grupo", "data_inicio", "data_fim")
    search_fields = ("titulo", "id_grupo__nome")


@admin.register(Conclusao)
class ConclusaoAdmin(admin.ModelAdmin):
    list_display = ("id_conclusao", "id_desafio", "id_usuario", "data_conclusao")
    search_fields = ("id_desafio__titulo", "id_usuario__nome")


# Registrar Usuario usando UsuarioAdmin
admin.site.register(Usuario, UsuarioAdmin)
