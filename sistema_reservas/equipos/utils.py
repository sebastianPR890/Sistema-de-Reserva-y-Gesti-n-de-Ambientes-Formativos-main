from .models import HistorialEquipo
from copy import deepcopy


def registrar_cambio_equipo(equipo_antes, equipo_despues, usuario, tipo_cambio='caracteristica', descripcion=''):
    """
    Registra automáticamente los cambios realizados en un equipo.

    Args:
        equipo_antes: Instancia del equipo ANTES de los cambios
        equipo_despues: Instancia del equipo DESPUÉS de los cambios
        usuario: Usuario que realizó el cambio
        tipo_cambio: Tipo de cambio (estado, ambiente, responsable, caracteristica, movimiento, otro)
        descripcion: Descripción adicional del cambio
    """
    campos_monitoreados = ['estado', 'ambiente', 'responsable', 'nombre', 'codigo', 'marca', 'modelo', 'serie', 'descripcion', 'activo']

    cambios_registrados = []

    for campo in campos_monitoreados:
        valor_anterior = getattr(equipo_antes, campo, None)
        valor_nuevo = getattr(equipo_despues, campo, None)

        # Convertir objetos a strings para comparación
        if hasattr(valor_anterior, 'id'):
            valor_anterior_str = str(valor_anterior)
        else:
            valor_anterior_str = str(valor_anterior) if valor_anterior is not None else ''

        if hasattr(valor_nuevo, 'id'):
            valor_nuevo_str = str(valor_nuevo)
        else:
            valor_nuevo_str = str(valor_nuevo) if valor_nuevo is not None else ''

        # Solo registrar si hubo cambio
        if valor_anterior_str != valor_nuevo_str:
            # Determinar tipo de cambio automáticamente si no está especificado
            tipo = tipo_cambio
            if campo == 'estado':
                tipo = 'estado'
            elif campo == 'ambiente':
                tipo = 'ambiente'
            elif campo == 'responsable':
                tipo = 'responsable'
            else:
                tipo = 'caracteristica'

            HistorialEquipo.objects.create(
                equipo=equipo_despues,
                tipo_cambio=tipo,
                campo=campo,
                valor_anterior=valor_anterior_str,
                valor_nuevo=valor_nuevo_str,
                usuario=usuario,
                descripcion=descripcion
            )
            cambios_registrados.append(campo)

    return cambios_registrados
