from .models import RegistroActividad
from django.forms.models import model_to_dict


def _obtener_ip(request):
    """Extrae la IP real del request, considerando proxies."""
    if not request:
        return None
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        return x_forwarded_for.split(',')[0].strip()
    return request.META.get('REMOTE_ADDR')


def _serializar_valor(valor):
    """Convierte un valor a una representación serializable para JSON."""
    if hasattr(valor, 'pk'):  # Es una instancia de modelo
        return f"{type(valor).__name__}({valor.pk}): {str(valor)}"
    elif isinstance(valor, bool):
        return 'Sí' if valor else 'No'
    elif valor is None:
        return 'N/A'
    else:
        return str(valor)


def registrar_actividad(usuario, accion, descripcion='', modulo='sistema',
                        request=None, tipo_accion='OTHER', objeto=None,
                        datos_antes=None, datos_despues=None):
    """
    Registra una actividad en el sistema.

    Parámetros:
    - usuario: Usuario que realiza la acción
    - accion: Descripción breve de la acción
    - descripcion: Descripción detallada
    - modulo: Módulo del sistema (reservas, usuarios, ambientes, equipos, sesion, sistema)
    - request: HttpRequest para obtener la IP
    - tipo_accion: CREATE, UPDATE, DELETE, LOGIN, LOGOUT, APPROVE, REJECT, CANCEL, EXPORT, OTHER
    - objeto: Instancia del modelo afectado
    - datos_antes: Dict con estado previo
    - datos_despues: Dict con estado posterior
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


def capturar_todos_campos(instancia):
    """
    Captura TODOS los campos de una instancia como dict.
    Excluye campos de relación inversa y métodos.
    """
    resultado = {}
    for campo in instancia._meta.fields:
        try:
            valor = getattr(instancia, campo.name)
            resultado[campo.name] = _serializar_valor(valor)
        except Exception as e:
            resultado[campo.name] = f"Error: {str(e)}"
    return resultado


def capturar_cambios(instancia_antes, instancia_despues, campos_a_comparar=None):
    """
    Compara dos instancias de un modelo y retorna los cambios.

    Si campos_a_comparar es None, compara TODOS los campos.

    Retorna:
    - Diccionario con los cambios: {'campo': {'antes': valor, 'después': valor}}
    """
    # Si no se especifican campos, usar todos
    if campos_a_comparar is None:
        campos_a_comparar = [f.name for f in instancia_antes._meta.fields]

    cambios = {}

    for campo in campos_a_comparar:
        try:
            valor_antes = getattr(instancia_antes, campo, None)
            valor_despues = getattr(instancia_despues, campo, None)

            valor_antes_str = _serializar_valor(valor_antes)
            valor_despues_str = _serializar_valor(valor_despues)

            if valor_antes_str != valor_despues_str:
                cambios[campo] = {
                    'antes': valor_antes_str,
                    'después': valor_despues_str
                }
        except Exception as e:
            cambios[campo] = {
                'antes': 'Error',
                'después': f'Error al comparar: {str(e)}'
            }

    return cambios


def registrar_actualizacion(usuario, objeto, cambios, modulo='sistema',
                             request=None, instancia=None):
    """
    Registra una actualización de un objeto capturando los cambios realizados.

    Parámetros:
    - usuario: Usuario que realiza la acción
    - objeto: Representación en string del objeto actualizado
    - cambios: Dict con {'campo': {'antes': valor_anterior, 'después': valor_nuevo}}
    - modulo: Módulo del sistema
    - request: HttpRequest para obtener la IP
    - instancia: Instancia del modelo afectado
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

