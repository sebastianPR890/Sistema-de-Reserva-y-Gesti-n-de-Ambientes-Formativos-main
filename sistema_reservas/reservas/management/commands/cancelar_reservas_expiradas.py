from django.core.management.base import BaseCommand
from reservas.models import Reserva


class Command(BaseCommand):
    help = 'Cancela automáticamente las reservas pendientes con más de 72 horas sin aprobación.'

    def handle(self, *args, **options):
        canceladas = Reserva.cancelar_expiradas()
        self.stdout.write(
            self.style.SUCCESS(f'{canceladas} reserva(s) cancelada(s) por expiración (72 horas sin aprobación).')
        )
