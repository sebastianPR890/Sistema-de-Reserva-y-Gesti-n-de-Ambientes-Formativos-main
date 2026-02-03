from django.urls import path
from . import views

app_name = 'login'

urlpatterns = [
    path('', views.login_view, name='login'),
    path('registro/', views.registro_view, name='registro'),
    path('logout/', views.logout_view, name='logout'),

    path('cambia_contraseña/<str:token>/', views.cambia_con, name='cambia_con'), 
    path('recuperar_contraseña/', views.recu_contra, name="recu_contra"), 
]
