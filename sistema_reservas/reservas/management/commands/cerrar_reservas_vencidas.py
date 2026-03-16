from django.core.management.base import BaseCommand
from reservas.models import Reserva


class Command(BaseCommand):
    help = 'Cierra reservas aprobadas vencidas y retira los equipos externos asociados.'

    def handle(self, *args, **options):
        # Cerrar reservas aprobadas vencidas
        cerradas = Reserva.cerrar_vencidas()
        if cerradas:
            self.stdout.write(self.style.SUCCESS(
                f'{cerradas} reserva(s) marcada(s) como completada(s) y sus equipos externos retirados.'
            ))
        else:
            self.stdout.write('No hay reservas vencidas pendientes de cerrar.')

        # También cancelar las pendientes sin aprobar > 72h
        canceladas = Reserva.cancelar_expiradas()
        if canceladas:
            self.stdout.write(self.style.WARNING(
                f'{canceladas} reserva(s) pendiente(s) cancelada(s) por superar 72h sin aprobación.'
            ))
