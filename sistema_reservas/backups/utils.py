import os
import subprocess
from datetime import datetime
from django.conf import settings
from pathlib import Path


def create_backup():
    """
    Crea un backup de la base de datos MySQL
    Returns: tuple (success: bool, message: str, filename: str)
    """
    try:
        # Obtener configuración de la base de datos
        db_config = settings.DATABASES['default']
        db_name = db_config['NAME']
        db_user = db_config['USER']
        db_password = db_config['PASSWORD']
        db_host = db_config.get('HOST', 'localhost')
        db_port = db_config.get('PORT', '3306')
        
        # Crear nombre del archivo con timestamp
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f'backup_{db_name}_{timestamp}.sql'
        filepath = os.path.join(settings.BACKUP_DIR, filename)
        
        # Comando mysqldump
        dump_command = [
            'mysqldump',
            f'--host={db_host}',
            f'--port={db_port}',
            f'--user={db_user}',
            f'--password={db_password}',
            '--single-transaction',
            '--quick',
            '--lock-tables=false',
            db_name
        ]
        
        # Ejecutar el backup
        with open(filepath, 'w') as backup_file:
            process = subprocess.Popen(
                dump_command,
                stdout=backup_file,
                stderr=subprocess.PIPE
            )
            _, error = process.communicate()
            
            if process.returncode != 0:
                error_message = error.decode('utf-8')
                return False, f'Error al crear backup: {error_message}', None
        
        # Limpiar backups antiguos
        clean_old_backups()
        
        # Obtener tamaño del archivo
        file_size = os.path.getsize(filepath)
        size_mb = round(file_size / (1024 * 1024), 2)
        
        return True, f'Backup creado exitosamente ({size_mb} MB)', filename
        
    except Exception as e:
        return False, f'Error inesperado: {str(e)}', None


def restore_backup(filename):
    """
    Restaura un backup de la base de datos
    Args:
    filename: nombre del archivo de backup
    Returns: tuple (success: bool, message: str)
    """
    try:
        filepath = os.path.join(settings.BACKUP_DIR, filename)
        
        if not os.path.exists(filepath):
            return False, 'El archivo de backup no existe'
        
        # Obtener configuración de la base de datos
        db_config = settings.DATABASES['default']
        db_name = db_config['NAME']
        db_user = db_config['USER']
        db_password = db_config['PASSWORD']
        db_host = db_config.get('HOST', 'localhost')
        db_port = db_config.get('PORT', '3306')
        
        # Comando mysql
        restore_command = [
            'mysql',
            f'--host={db_host}',
            f'--port={db_port}',
            f'--user={db_user}',
            f'--password={db_password}',
            db_name
        ]
        
        # Ejecutar la restauración
        with open(filepath, 'r') as backup_file:
            process = subprocess.Popen(
                restore_command,
                stdin=backup_file,
                stderr=subprocess.PIPE
            )
            _, error = process.communicate()
            
            if process.returncode != 0:
                error_message = error.decode('utf-8')
                return False, f'Error al restaurar backup: {error_message}'
        
        return True, 'Base de datos restaurada exitosamente'
        
    except Exception as e:
        return False, f'Error inesperado: {str(e)}'


def get_backups_list():
    """
    Obtiene la lista de backups disponibles con su información
    Returns: list of dict con información de cada backup
    """
    backups = []
    backup_dir = settings.BACKUP_DIR
    
    if not os.path.exists(backup_dir):
        return backups
    
    for filename in os.listdir(backup_dir):
        if filename.endswith('.sql'):
            filepath = os.path.join(backup_dir, filename)
            file_stat = os.stat(filepath)
            
            backups.append({
                'filename': filename,
                'size': round(file_stat.st_size / (1024 * 1024), 2),  # MB
                'date': datetime.fromtimestamp(file_stat.st_mtime),
                'path': filepath
            })
    
    # Ordenar por fecha (más reciente primero)
    backups.sort(key=lambda x: x['date'], reverse=True)
    
    return backups


def delete_backup(filename):
    """
    Elimina un archivo de backup
    Args:
        filename: nombre del archivo a eliminar
    Returns: tuple (success: bool, message: str)
    """
    try:
        filepath = os.path.join(settings.BACKUP_DIR, filename)
        
        if not os.path.exists(filepath):
            return False, 'El archivo no existe'
        
        os.remove(filepath)
        return True, 'Backup eliminado exitosamente'
        
    except Exception as e:
        return False, f'Error al eliminar: {str(e)}'


def clean_old_backups():
    """
    Limpia backups antiguos manteniendo solo MAX_BACKUPS
    """
    try:
        backups = get_backups_list()
        max_backups = getattr(settings, 'MAX_BACKUPS', 10)
        
        if len(backups) > max_backups:
            # Eliminar los backups más antiguos
            for backup in backups[max_backups:]:
                os.remove(backup['path'])
                
    except Exception as e:
        print(f'Error al limpiar backups antiguos: {str(e)}')