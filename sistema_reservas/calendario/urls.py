from django.urls import path
from . import views

app_name = 'calendario'

urlpatterns = [
    path('', views.vista_calendario, name='calendario'),
    path('api/reservas/', views.get_reservas, name='get_reservas'),
]
