from .models import RegistroActividad
import json


def registrar_actividad(usuario, accion, descripcion='', modulo='sistema', request=None):
    """Registra una actividad en el sistema."""
    ip = None
    if request:
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0].strip()
        else:
            ip = request.META.get('REMOTE_ADDR')

    RegistroActividad.objects.create(
        usuario=usuario,
        accion=accion,
        descripcion=descripcion,
        modulo=modulo,
        ip_address=ip,
    )


def registrar_actualizacion(usuario, objeto, cambios, modulo='sistema', request=None):
    """
    Registra una actualización de un objeto capturando los cambios realizados.
    
    Parámetros:
    - usuario: Usuario que realiza la acción
    - objeto: Objeto actualizado (con su representación en string)
    - cambios: Diccionario con {'campo': {'antes': valor_anterior, 'después': valor_nuevo}}
    - modulo: Módulo del sistema donde ocurre la acción
    - request: HttpRequest para obtener la IP
    """
    if not cambios:
        return  # No hay cambios para registrar
    
    ip = None
    if request:
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0].strip()
        else:
            ip = request.META.get('REMOTE_ADDR')

    # Construir descripción de los cambios
    cambios_formateados = []
    for campo, valores in cambios.items():
        antes = valores.get('antes', '')
        despues = valores.get('después', '')
        cambios_formateados.append(f"{campo}: '{antes}' → '{despues}'")
    
    descripcion = "Cambios realizados:\n" + "\n".join(cambios_formateados)
    
    RegistroActividad.objects.create(
        usuario=usuario,
        accion=f'Actualización de {objeto}',
        descripcion=descripcion,
        modulo=modulo,
        ip_address=ip,
    )


def capturar_cambios(instancia_antes, instancia_despues, campos_a_comparar):
    """
    Compara dos instancias de un modelo y retorna los cambios en los campos especificados.
    
    Parámetros:
    - instancia_antes: Instancia antes de los cambios
    - instancia_despues: Instancia después de los cambios
    - campos_a_comparar: Lista de nombres de campos a comparar
    
    Retorna:
    - Diccionario con los cambios: {'campo': {'antes': valor, 'después': valor}}
    """
    cambios = {}
    
    for campo in campos_a_comparar:
        valor_antes = getattr(instancia_antes, campo, None)
        valor_despues = getattr(instancia_despues, campo, None)
        
        # Mostrar campos booleanos de forma legible
        if isinstance(valor_antes, bool):
            valor_antes = 'Sí' if valor_antes else 'No'
        if isinstance(valor_despues, bool):
            valor_despues = 'Sí' if valor_despues else 'No'
        
        if valor_antes != valor_despues:
            cambios[campo] = {
                'antes': str(valor_antes),
                'después': str(valor_despues)
            }
    
    return cambios
