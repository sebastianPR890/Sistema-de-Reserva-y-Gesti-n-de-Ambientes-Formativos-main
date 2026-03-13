from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='RegistroActividad',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('accion', models.CharField(max_length=200)),
                ('descripcion', models.TextField(blank=True)),
                ('modulo', models.CharField(
                    choices=[
                        ('reservas', 'Reservas'),
                        ('usuarios', 'Usuarios'),
                        ('ambientes', 'Ambientes'),
                        ('equipos', 'Equipos'),
                        ('sesion', 'Sesión'),
                        ('sistema', 'Sistema'),
                    ],
                    default='sistema',
                    max_length=20,
                )),
                ('ip_address', models.GenericIPAddressField(blank=True, null=True)),
                ('fecha', models.DateTimeField(auto_now_add=True)),
                ('usuario', models.ForeignKey(
                    blank=True,
                    null=True,
                    on_delete=django.db.models.deletion.SET_NULL,
                    related_name='actividades',
                    to=settings.AUTH_USER_MODEL,
                )),
            ],
            options={
                'verbose_name': 'Registro de Actividad',
                'verbose_name_plural': 'Registros de Actividad',
                'db_table': 'actividad_registros',
                'ordering': ['-fecha'],
            },
        ),
    ]
