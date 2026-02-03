from django.urls import path
from . import views

app_name = 'backups'

urlpatterns = [
    path('', views.backup_dashboard, name='backup_dashboard'),
    path('create/', views.create_backup_view, name='create_backup'),
    path('restore/<str:filename>/', views.restore_backup_view, name='restore_backup'),
    path('delete/<str:filename>/', views.delete_backup_view, name='delete_backup'),
    path('download/<str:filename>/', views.download_backup_view, name='download_backup'),
]