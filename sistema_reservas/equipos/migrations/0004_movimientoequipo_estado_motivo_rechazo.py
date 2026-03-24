from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('equipos', '0003_remove_equipo_fecha_adquisicion_remove_equipo_valor'),
    ]

    operations = [
        migrations.AddField(
            model_name='movimientoequipo',
            name='estado',
            field=models.CharField(
                choices=[
                    ('pendiente', 'Pendiente'),
                    ('autorizado', 'Autorizado'),
                    ('rechazado', 'Rechazado'),
                ],
                default='pendiente',
                max_length=20,
            ),
        ),
        migrations.AddField(
            model_name='movimientoequipo',
            name='motivo_rechazo',
            field=models.TextField(blank=True, default=''),
            preserve_default=False,
        ),
    ]
