from django.urls import path
from . import views

app_name = 'equipos'

urlpatterns = [
    # URLs para Equipos
    path('', views.EquipoListView.as_view(), name='lista'),
    path('crear/', views.EquipoCreateView.as_view(), name='equipo_crear'),
    path('<int:pk>/', views.EquipoDetailView.as_view(), name='equipo_detalle'),
    path('<int:pk>/editar/', views.EquipoUpdateView.as_view(), name='equipo_editar'),
    path('<int:pk>/eliminar/', views.EquipoDeleteView.as_view(), name='equipo_eliminar'),

    # URLs para Movimientos de Equipo
    path('movimientos/crear/', views.MovimientoEquipoCreateView.as_view(), name='movimiento_crear'),
    path('movimientos/', views.MovimientoEquipoListView.as_view(), name='lista_movimientos'),
    path('movimientos/<int:pk>/autorizar/', views.autorizar_movimiento, name='movimiento_autorizar'),
    path('movimientos/<int:pk>/rechazar/', views.rechazar_movimiento, name='movimiento_rechazar'),
]