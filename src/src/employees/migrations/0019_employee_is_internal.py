# Migración que agrega el campo is_internal al modelo Employee.
#
# is_internal=True corresponde al personal fijo interno (comportamiento por
# defecto para todos los registros existentes). Los registros con
# is_internal=False se comportan como "trabajadores fantasma" del comedor y
# no afectan los cálculos de asistencia del personal fijo.

from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("employees", "0018_employee_is_actived"),
    ]

    operations = [
        migrations.AddField(
            model_name="employee",
            name="is_internal",
            field=models.BooleanField(
                default=True,
                help_text=(
                    "Indica si el trabajador es personal fijo interno de la empresa. "
                    "Los registros con is_internal=False se comportan como trabajadores "
                    "fantasmas: no requieren marcar asistencia para recibir beneficios del "
                    "comedor y no afectan los cálculos de asistencia del personal fijo."
                ),
                verbose_name="Personal interno",
            ),
        ),
    ]
