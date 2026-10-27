"""Da un `user_key` propio a los usuarios que comparten uno.

Hasta marzo de 2026 `user_key` usaba `default=uuid.uuid4()`: el UUID se
calculaba al arrancar el servidor y los usuarios registrados hasta el
siguiente reinicio recibian el mismo. La migracion siguiente agrega
`unique=True`, que fallaria con esas claves repetidas.

Misma regla que el comando `fix_duplicate_user_keys`: en cada grupo el usuario
mas antiguo conserva la clave y los demas reciben una nueva. Se separa de la
migracion del indice para no mezclar cambios de datos y de esquema en la misma
transaccion de PostgreSQL.
"""

import uuid

from django.db import migrations
from django.db.models import Count


def fix_duplicate_user_keys(apps, schema_editor):
    User = apps.get_model("user", "User")
    duplicated_keys = (
        User.objects.values("user_key")
        .annotate(total=Count("id"))
        .filter(total__gt=1)
        .values_list("user_key", flat=True)
    )
    for key in list(duplicated_keys):
        user_ids = list(User.objects.filter(user_key=key).order_by("id").values_list("id", flat=True))
        for user_id in user_ids[1:]:
            new_key = uuid.uuid4()
            while User.objects.filter(user_key=new_key).exists():
                new_key = uuid.uuid4()
            # `update` no toca `modified`.
            User.objects.filter(pk=user_id).update(user_key=new_key)


class Migration(migrations.Migration):

    dependencies = [
        ("user", "0007_remove_user_location_fk"),
    ]

    operations = [
        migrations.RunPython(fix_duplicate_user_keys, migrations.RunPython.noop),
    ]
