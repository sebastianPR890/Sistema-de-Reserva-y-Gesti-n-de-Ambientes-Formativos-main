from .models import RegistroActividad


def _obtener_ip(request):
    """Extrae la IP real del request, considerando proxies."""
    if not request:
        return None
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        return x_forwarded_for.split(',')[0].strip()
    return request.META.get('REMOTE_ADDR')


def registrar_actividad(usuario, accion, descripcion='', modulo='sistema',
                        request=None, tipo_accion='OTHER', objeto=None,
                        datos_antes=None, datos_despues=None):
    """
    Registra una actividad en el sistema.

    Parámetros nuevos (opcionales para retrocompatibilidad):
    - tipo_accion: Clave de RegistroActividad.TIPOS_ACCION (CREATE, UPDATE, DELETE, etc.)
    - objeto: Instancia del modelo afectado; se extraen objeto_tipo y objeto_id automáticamente.
    - datos_antes: Dict con el estado previo del objeto (para auditoría de cambios).
    - datos_despues: Dict con el estado posterior del objeto.
    """
    RegistroActividad.objects.create(
        usuario=usuario,
        accion=accion,
        descripcion=descripcion,
        modulo=modulo,
        tipo_accion=tipo_accion,
        objeto_tipo=type(objeto).__name__ if objeto else '',
        objeto_id=objeto.pk if objeto else None,
        datos_antes=datos_antes,
        datos_despues=datos_despues,
        ip_address=_obtener_ip(request),
    )


def registrar_actualizacion(usuario, objeto, cambios, modulo='sistema',
                             request=None, instancia=None):
    """
    Registra una actualización de un objeto capturando los cambios realizados.

    Parámetros:
    - usuario: Usuario que realiza la acción.
    - objeto: Representación en string del objeto actualizado.
    - cambios: Dict con {'campo': {'antes': valor_anterior, 'después': valor_nuevo}}.
    - modulo: Módulo del sistema donde ocurre la acción.
    - request: HttpRequest para obtener la IP.
    - instancia: Instancia del modelo afectado (nuevo, opcional). Permite registrar
                 objeto_tipo, objeto_id, datos_antes y datos_despues automáticamente.
    """
    if not cambios:
        return

    cambios_formateados = []
    datos_antes = {}
    datos_despues = {}

    for campo, valores in cambios.items():
        antes = valores.get('antes', '')
        despues = valores.get('después', '')
        cambios_formateados.append(f"{campo}: '{antes}' → '{despues}'")
        datos_antes[campo] = antes
        datos_despues[campo] = despues

    descripcion = "Cambios realizados:\n" + "\n".join(cambios_formateados)

    RegistroActividad.objects.create(
        usuario=usuario,
        accion=f'Actualización de {objeto}',
        descripcion=descripcion,
        modulo=modulo,
        tipo_accion='UPDATE',
        objeto_tipo=type(instancia).__name__ if instancia else '',
        objeto_id=instancia.pk if instancia else None,
        datos_antes=datos_antes,
        datos_despues=datos_despues,
        ip_address=_obtener_ip(request),
    )


def capturar_cambios(instancia_antes, instancia_despues, campos_a_comparar):
    """
    Compara dos instancias de un modelo y retorna los cambios en los campos especificados.

    Retorna:
    - Diccionario con los cambios: {'campo': {'antes': valor, 'después': valor}}
    """
    cambios = {}

    for campo in campos_a_comparar:
        valor_antes = getattr(instancia_antes, campo, None)
        valor_despues = getattr(instancia_despues, campo, None)

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
