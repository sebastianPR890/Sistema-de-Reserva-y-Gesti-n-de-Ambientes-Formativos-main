from django.urls import path
from . import views

app_name = 'reservas'

urlpatterns = [
    path('', views.index, name='index'),
    path('reservas/', views.lista_reservas, name='lista_reservas'),
    path('crear/', views.crear_reserva, name='crear_reserva'),
    path('<int:pk>/editar/', views.editar_reserva, name='editar_reserva'),
    path('manual/', views.manual_usuario, name='manual_usuario'),
    path('reporte/pdf/', views.descargar_reporte_pdf, name='descargar_reporte_pdf'),
    path('reserva/<int:pk>/aprobar/', views.aprobar_reserva, name='aprobar_reserva'),
    path('reserva/<int:pk>/rechazar/', views.rechazar_reserva, name='rechazar_reserva'),
    path('reserva/<int:pk>/cancelar/', views.cancelar_reserva, name='cancelar_reserva'),
    path('calendario/api/reservas/', views.obtener_reservas_calendario, name='api_reservas_calendario'),
    path('calendario/crear/', views.crear_reserva_calendario, name='crear_reserva_calendario'),
]
