from .models import HistorialReserva
from copy import deepcopy


def registrar_cambio_reserva(reserva_antes, reserva_despues, usuario, tipo_cambio='detalles', descripcion=''):
    """
    Registra automáticamente los cambios realizados en una reserva.

    Args:
        reserva_antes: Instancia de la reserva ANTES de los cambios
        reserva_despues: Instancia de la reserva DESPUÉS de los cambios
        usuario: Usuario que realizó el cambio
        tipo_cambio: Tipo de cambio (estado, fechas, ambiente, detalles, aprobacion, rechazo, cancelacion, otro)
        descripcion: Descripción adicional del cambio
    """
    campos_monitoreados = ['estado', 'fecha_inicio', 'fecha_fin', 'ambiente', 'proposito', 'numero_asistentes', 'observaciones']

    cambios_registrados = []

    for campo in campos_monitoreados:
        valor_anterior = getattr(reserva_antes, campo, None)
        valor_nuevo = getattr(reserva_despues, campo, None)

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
            if campo in ['fecha_inicio', 'fecha_fin']:
                tipo = 'fechas'
            elif campo == 'estado':
                tipo = 'estado'
            elif campo == 'ambiente':
                tipo = 'ambiente'
            else:
                tipo = 'detalles'

            HistorialReserva.objects.create(
                reserva=reserva_despues,
                tipo_cambio=tipo,
                campo=campo,
                valor_anterior=valor_anterior_str,
                valor_nuevo=valor_nuevo_str,
                usuario=usuario,
                descripcion=descripcion
            )
            cambios_registrados.append(campo)

    return cambios_registrados
