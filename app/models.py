from django.db import models
from django.contrib.auth.models import (
    AbstractBaseUser,
    BaseUserManager,
    PermissionsMixin,
)
from django.utils import timezone
from django.contrib.auth.models import User
from django.conf import settings

class UsuarioManager(BaseUserManager):
    def create_user(self, nome, password=None, email=None, **extra_fields):
        if not nome:
            raise ValueError("O usuário deve ter um nome de usuário")

        user = self.model(
            nome=nome,
            email=self.normalize_email(email) if email else None,
            **extra_fields
        )
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, nome, password=None, email=None, **extra_fields):
        extra_fields.setdefault("is_staff", True)
        extra_fields.setdefault("is_superuser", True)

        if extra_fields.get("is_staff") is not True:
            raise ValueError("Superuser precisa ter is_staff=True.")
        if extra_fields.get("is_superuser") is not True:
            raise ValueError("Superuser precisa ter is_superuser=True.")
        if not password:
            raise ValueError("Superusers precisam de senha.")

        return self.create_user(nome, password=password, email=email, **extra_fields)

class Usuario(AbstractBaseUser, PermissionsMixin):
    id_usuario = models.AutoField(primary_key=True)
    nome = models.CharField(max_length=150, unique=True)  # 👈 será o username
    email = models.EmailField(unique=True, null=True, blank=True)
    idade = models.DateField(null=True, blank=True)

    foto_perfil = models.ImageField(
        upload_to='profile_pics/',
        null=True,
        blank=True,
        default='profile_pics/default-avatar.png'
    )

    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)
    date_joined = models.DateTimeField(default=timezone.now)

    USERNAME_FIELD = "nome"
    REQUIRED_FIELDS = ["email"]

    objects = UsuarioManager()

    class Meta:
        db_table = "usuarios"

    def __str__(self):
        return self.nome

class Preferencia(models.Model):
    SEXO_CHOICES = [
        ("M", "Masculino"),
        ("F", "Feminino"),
        ("O", "Outro"),
    ]

    NIVEL_CHOICES = [
        ("I", "Iniciante"),
        ("M", "Intermediário"),
        ("A", "Avançado"),
    ]

    TURNO_CHOICES = [
        ("M", "Manhã"),
        ("T", "Tarde"),
        ("N", "Noite"),
    ]

    id_preferencia = models.AutoField(primary_key=True)
    usuario = models.ForeignKey(Usuario, on_delete=models.CASCADE, related_name="preferencias")
    esportes = models.CharField(max_length=200, blank=True)
    sexo = models.CharField(max_length=1, choices=SEXO_CHOICES, blank=True)
    nivel = models.CharField(max_length=1, choices=NIVEL_CHOICES, blank=True)
    turno = models.CharField(max_length=1, choices=TURNO_CHOICES, blank=True)
    idade_parc = models.IntegerField(null=True, blank=True)  # 👈 melhor usar IntegerField

    class Meta:
        db_table = "preferencias"

    def __str__(self):
        return f"Pref {self.id_preferencia} - {self.usuario.nome}"

class Parceiro(models.Model):
    id_parceiros = models.AutoField(primary_key=True)
    usuario = models.ForeignKey(Usuario, on_delete=models.CASCADE, related_name="parceiros")
    preferencia = models.ForeignKey(Preferencia, on_delete=models.SET_NULL, null=True, blank=True)
    localizacao = models.CharField(max_length=255, blank=True)

    class Meta:
        db_table = "parceiros"

    def __str__(self):
        return f"Parceiro {self.id_parceiros} - {self.usuario.nome}"

class Ranking(models.Model):
    id_ranking = models.AutoField(primary_key=True)
    usuario = models.ForeignKey(Usuario, on_delete=models.CASCADE, related_name="rankings")
    pontuacao_total = models.IntegerField(default=0)
    esporte_prat = models.CharField(max_length=150, blank=True)

    class Meta:
        db_table = "ranking"

    def __str__(self):
        return f"{self.usuario.nome} - {self.pontuacao_total}"

class Mensagem(models.Model):
    id_mensagem = models.AutoField(primary_key=True)
    id_remetente = models.ForeignKey(Usuario, on_delete=models.CASCADE, related_name="mensagens_enviadas")
    id_destinatario = models.ForeignKey(Usuario, on_delete=models.CASCADE, related_name="mensagens_recebidas")
    mensagem = models.TextField()
    hora = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "mensagens"
        ordering = ["hora"]

    def __str__(self):
        return f"De {self.id_remetente.nome} para {self.id_destinatario.nome} - {self.hora}"

class Grupo(models.Model):
    id_grupo = models.AutoField(primary_key=True)
    nome = models.CharField(max_length=200)
    descricao = models.TextField(blank=True)
    localizacao = models.CharField(max_length=255, blank=True)
    criado_em = models.DateTimeField(auto_now_add=True)
    membros = models.ManyToManyField(Usuario, related_name="grupos", blank=True)

    class Meta:
        db_table = "grupos"

    def __str__(self):
        return self.nome

class MensagemGrupo(models.Model):
    id_mensagem = models.AutoField(primary_key=True)
    id_grupo = models.ForeignKey(Grupo, on_delete=models.CASCADE, related_name="mensagens")
    id_remetente = models.ForeignKey(Usuario, on_delete=models.CASCADE, related_name="mensagens_grupo_enviadas")
    mensagem = models.TextField()
    hora = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "mensagens_grupo"
        ordering = ["hora"]

    def __str__(self):
        return f"Em {self.id_grupo.nome} de {self.id_remetente.nome} - {self.hora}"

class GrupoAdmin(models.Model):
    id = models.AutoField(primary_key=True)
    grupo = models.ForeignKey(Grupo, on_delete=models.CASCADE, related_name="admins")
    usuario = models.ForeignKey(Usuario, on_delete=models.CASCADE, related_name="admin_de_grupos")

    class Meta:
        db_table = "grupo_admins"
        unique_together = ("grupo", "usuario")

    def __str__(self):
        return f"Admin {self.usuario.nome} de {self.grupo.nome}"

class Desafio(models.Model):
    id_desafio = models.AutoField(primary_key=True)
    id_grupo = models.ForeignKey(Grupo, on_delete=models.CASCADE, related_name="desafios")
    titulo = models.CharField(max_length=200)
    descricao = models.TextField(blank=True)
    data_inicio = models.DateField()
    data_fim = models.DateField()

    class Meta:
        db_table = "desafios"

    def __str__(self):
        return f"{self.titulo} ({self.id_grupo.nome})"

class Conclusao(models.Model):
    id_conclusao = models.AutoField(primary_key=True)
    id_desafio = models.ForeignKey(Desafio, on_delete=models.CASCADE, related_name="conclusoes")
    id_usuario = models.ForeignKey(Usuario, on_delete=models.CASCADE, related_name="conclusoes")
    data_conclusao = models.DateField(auto_now_add=True)

    class Meta:
        db_table = "conclusoes"
        unique_together = ("id_desafio", "id_usuario")

    def __str__(self):
        return f"{self.id_usuario.nome} concluiu {self.id_desafio.titulo}"

class Comunidade(models.Model):
    nome = models.CharField(max_length=100)
    admin = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='comunidades_admin'
    )
    membros = models.ManyToManyField(
        settings.AUTH_USER_MODEL,
        related_name='comunidades'
    )
    cor = models.CharField(max_length=20, default="#FFB6C1")  # cor da caixa

    @property
    def total_membros(self):
        return self.membros.count()


    def __str__(self):
        return self.nome
