from django.urls import path
from . import views

app_name = 'notificaciones'

urlpatterns = [
    path('', views.listar_notificaciones, name='listar_notificaciones'),
    path('<int:pk>/marcar_leida/', views.marcar_como_leida, name='marcar_como_leida'),
    path('marcar_todas_leidas/', views.marcar_como_leidas_masiva, name='marcar_todas_leidas'),
    path('contar_no_leidas/', views.contar_no_leidas, name='contar_no_leidas'),
]