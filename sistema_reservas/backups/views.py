from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib import messages
from django.http import FileResponse, Http404
import os
from django.conf import settings
from .utils import create_backup, restore_backup, get_backups_list, delete_backup


def is_admin(user):
    """Verifica que el usuario sea administrador"""
    return user.is_authenticated and (user.is_superuser or user.is_staff)


@login_required
@user_passes_test(is_admin)
def backup_dashboard(request):
    """Vista principal del dashboard de backups"""
    backups = get_backups_list()
    
    context = {
        'backups': backups,
        'total_backups': len(backups),
    }
    
    return render(request, 'backups/backup_dashboard.html', context)


@login_required
@user_passes_test(is_admin)
def create_backup_view(request):
    """Crea un nuevo backup"""
    if request.method == 'POST':
        success, message, filename = create_backup()
        
        if success:
            messages.success(request, message)
        else:
            messages.error(request, message)
    
    return redirect('backups:backup_dashboard')


@login_required
@user_passes_test(is_admin)
def restore_backup_view(request, filename):
    """Restaura un backup específico"""
    if request.method == 'POST':
        # Confirmación de seguridad
        confirm = request.POST.get('confirm')
        
        if confirm == 'yes':
            success, message = restore_backup(filename)
            
            if success:
                messages.success(request, message)
            else:
                messages.error(request, message)
        else:
            messages.warning(request, 'Restauración cancelada')
    
    return redirect('backups:backup_dashboard')


@login_required
@user_passes_test(is_admin)
def delete_backup_view(request, filename):
    """Elimina un backup"""
    if request.method == 'POST':
        success, message = delete_backup(filename)
        
        if success:
            messages.success(request, message)
        else:
            messages.error(request, message)
    
    return redirect('backups:backup_dashboard')


@login_required
@user_passes_test(is_admin)
def download_backup_view(request, filename):
    """Descarga un archivo de backup"""
    filepath = os.path.join(settings.BACKUP_DIR, filename)
    
    if not os.path.exists(filepath):
        raise Http404("Backup no encontrado")
    
    response = FileResponse(open(filepath, 'rb'), content_type='application/sql')
    response['Content-Disposition'] = f'attachment; filename="{filename}"'
    
    return response