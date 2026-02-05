from django.urls import path
from . import views

app_name = 'usuarios'

urlpatterns = [
    path('', views.lista_usuarios, name='lista_usuarios'),
    path('<int:pk>/', views.detalle_usuario, name='detalle_usuario'),
    path('perfil/', views.perfil_usuario, name='perfil'),
    path('perfil/editar/', views.editar_perfil, name='editar_perfil'),
    path('solicitar-cambio-rol/', views.solicitar_cambio_rol, name='solicitar_cambio_rol'),
    path('<int:pk>/editar/', views.editar_usuario, name='editar_usuario'),
    # Gestión de solicitudes de rol (solo administradores)
    path('solicitudes-rol/', views.lista_solicitudes_rol, name='lista_solicitudes_rol'),
    path('solicitudes-rol/<int:pk>/aprobar/', views.aprobar_solicitud_rol, name='aprobar_solicitud_rol'),
    path('solicitudes-rol/<int:pk>/rechazar/', views.rechazar_solicitud_rol, name='rechazar_solicitud_rol'),
]
