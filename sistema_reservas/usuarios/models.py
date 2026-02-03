from django.contrib.auth.models import AbstractUser, UserManager as BaseUserManager
from django.db import models
from django.core.validators import RegexValidator
from django.utils import timezone


class UsuarioManager(BaseUserManager):
    """Manager personalizado que usa documento en lugar de username."""

    def _create_user(self, documento, email, password, **extra_fields):
        if not documento:
            raise ValueError('El documento es obligatorio.')
        email = self.normalize_email(email)
        extra_fields.setdefault('username', documento)
        user = self.model(documento=documento, email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_user(self, documento, email=None, password=None, **extra_fields):
        extra_fields.setdefault('is_staff', False)
        extra_fields.setdefault('is_superuser', False)
        return self._create_user(documento, email, password, **extra_fields)

    def create_superuser(self, documento, email=None, password=None, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        extra_fields.setdefault('rol', 'admin')
        extra_fields.setdefault('activo', True)
        return self._create_user(documento, email, password, **extra_fields)


class Usuario(AbstractUser):
    """Modelo personalizado de usuario que extiende AbstractUser."""
    
    ROLES = [
        ('instructor', 'Instructor'),
        ('administrativo', 'Administrativo'),
        ('coordinador', 'Coordinador'),
        ('admin', 'Administrador'),
        ('usuario', 'Usuario'),
    ]
    
    documento = models.CharField(
        max_length=20, 
        unique=True, 
        validators=[RegexValidator(regex=r'^\d+$', message='Solo números')]
    )
    nombres = models.CharField(max_length=100)
    apellidos = models.CharField(max_length=100)
    telefono = models.CharField(max_length=15, blank=True)
    rol = models.CharField(max_length=20, choices=ROLES, default='usuario')
    activo = models.BooleanField(default=True)
    fecha_creacion = models.DateTimeField(auto_now_add=True)
    fecha_actualizacion = models.DateTimeField(auto_now=True)
    
    username = models.CharField(max_length=150, unique=True)
    first_name = models.CharField(max_length=30, blank=True, null=True)
    last_name = models.CharField(max_length=150, blank=True, null=True)
    
    objects = UsuarioManager()

    USERNAME_FIELD = 'documento'
    REQUIRED_FIELDS = ['email', 'nombres', 'apellidos']
    
    class Meta:
        verbose_name = 'Usuario'
        verbose_name_plural = 'Usuarios'
        db_table = 'usuarios'
        ordering = ['apellidos', 'nombres']
    
    def save(self, *args, **kwargs):
        """Sincroniza campos antes de guardar el usuario."""
        self.username = self.documento
        self.first_name = self.nombres
        self.last_name = self.apellidos
            
        self.is_active = self.activo
        super().save(*args, **kwargs)
    
    def nombre_completo(self):
        """Retorna el nombre completo del usuario."""
        return f"{self.nombres} {self.apellidos}"
    
    def puede_aprobar_reservas(self):
        """Verifica si el usuario puede aprobar reservas."""
        return self.rol in ['coordinador', 'admin']
    
    def get_rol_display(self):
        """Retorna el nombre legible del rol."""
        for valor, nombre in self.ROLES:
            if valor == self.rol:
                return nombre
        return self.rol
    
    def __str__(self):
        return f"{self.documento} - {self.nombre_completo()}"