"""Registro de vistas y descargas de objetos de aprendizaje.

Reglas:

- la referencia la emite `interaction-ref` firmada con la `SECRET_KEY`; una
  referencia inventada o alterada no suma
- con referencia válida se suma una vista y una descarga por referencia, por
  OA y por día (la fecha es la del servidor)
- sin referencia no se suma, salvo con `INTERACTION_ALLOW_MISSING_REFERENCE`
  (compatibilidad con un frontend que no la envía)
- el número que envía el cliente nunca se usa: el backend solo suma 1
- los registros de días anteriores se borran solos con la primera
  interacción de cada día
"""

import logging

import shortuuid
from django.conf import settings
from django.core import signing
from django.core.cache import cache
from django.db import transaction
from django.db.models import F, IntegerField, OuterRef, Subquery, Sum, Value
from django.db.models.functions import Coalesce
from django.utils import timezone

from applications.interaction.models import DownloadRecord, Interaction, ViewInteraction, ViewRecord
from applications.learning_object_metadata.models import LearningObjectMetadata


logger = logging.getLogger(__name__)

REFERENCE_SALT = 'applications.interaction.reference'
REFERENCE_LENGTH = 64
CLEANUP_CACHE_KEY = 'interaction_records_cleanup:{date}'
CLEANUP_CACHE_TIMEOUT = 60 * 60 * 24

_signer = signing.Signer(salt=REFERENCE_SALT)


def issue_reference():
    """Devuelve una referencia nueva con la forma `valor_aleatorio:firma`."""

    return _signer.sign(shortuuid.ShortUUID().random(length=REFERENCE_LENGTH))


def read_reference(reference):
    """Devuelve el valor aleatorio si la firma es válida; si no, `None`."""

    try:
        value = _signer.unsign(reference)
    except signing.BadSignature:
        return None
    if len(value) != REFERENCE_LENGTH:
        return None
    return value


def _should_count(record_model, learning_object, reference):
    """Decide si la interacción suma y registra la referencia del día.

    Debe llamarse con el OA bloqueado, para que dos peticiones iguales al mismo
    tiempo no sumen las dos.
    """

    if not reference:
        return getattr(settings, 'INTERACTION_ALLOW_MISSING_REFERENCE', False)

    value = read_reference(reference)
    if value is None:
        return False

    _, created = record_model.objects.get_or_create(
        reference=value,
        learning_object=learning_object,
        date=timezone.localdate(),
    )
    return created


def _lock_learning_object(learning_object):
    """Bloquea la fila del OA hasta el fin de la transacción."""

    LearningObjectMetadata.objects.select_for_update().only('id').get(pk=learning_object.pk)


def _get_view_counter(learning_object):
    """Devuelve la única fila de vistas del OA.

    Si hay varias (creadas por el flujo anterior), las junta en la más antigua
    sumando sus valores, y borra las demás.
    """

    counters = list(ViewInteraction.objects.filter(learning_object=learning_object).order_by('id'))
    if not counters:
        return ViewInteraction.objects.create(learning_object=learning_object, view=0)

    counter, duplicates = counters[0], counters[1:]
    if duplicates:
        counter.view = sum(item.view for item in counters)
        counter.save(update_fields=['view', 'modified'])
        ViewInteraction.objects.filter(pk__in=[item.pk for item in duplicates]).delete()
    return counter


def get_view_total(learning_object_id):
    """Total de vistas del OA, o `None` si todavía no tiene registro."""

    return ViewInteraction.objects.filter(learning_object_id=learning_object_id).aggregate(
        total=Sum('view'),
    )['total']


def counter_total_subquery(model, value_field):
    """Subquery con la suma de un contador por OA (0 si no hay filas).

    Suma todas las filas del OA porque `ViewInteraction` puede tener más de
    una por OA e `Interaction` guarda una por usuario. Se usa para anotar
    `views` y `downloads` en listados de OA sin una consulta por cada uno.
    """

    total = (
        model.objects
        .filter(learning_object=OuterRef('pk'))
        .values('learning_object')
        .annotate(total=Sum(value_field))
        .values('total')
    )
    return Coalesce(Subquery(total, output_field=IntegerField()), Value(0))


def cleanup_old_records():
    """Borra los registros de días anteriores una sola vez por día.

    `cache.add` solo devuelve `True` a la primera petición del día, así que el
    borrado se ejecuta una vez para todo el servidor.
    """

    today = timezone.localdate()
    if not cache.add(CLEANUP_CACHE_KEY.format(date=today.isoformat()), True, CLEANUP_CACHE_TIMEOUT):
        return
    ViewRecord.objects.filter(date__lt=today).delete()
    DownloadRecord.objects.filter(date__lt=today).delete()


def register_view(learning_object, reference=None):
    """Suma una vista si corresponde y devuelve la fila de vistas del OA."""

    cleanup_old_records()
    with transaction.atomic():
        _lock_learning_object(learning_object)
        counter = _get_view_counter(learning_object)
        if _should_count(ViewRecord, learning_object, reference):
            ViewInteraction.objects.filter(pk=counter.pk).update(view=F('view') + 1)
            counter.refresh_from_db(fields=['view'])
    return counter


def register_download(learning_object, user, reference=None):
    """Suma una descarga si corresponde y devuelve la fila del usuario con el OA.

    Las descargas se guardan en la fila `Interaction` del usuario, que se crea
    si todavía no existe.
    """

    cleanup_old_records()
    with transaction.atomic():
        _lock_learning_object(learning_object)
        interaction = Interaction.objects.filter(
            learning_object=learning_object,
            user=user,
        ).order_by('id').first()
        if interaction is None:
            interaction = Interaction.objects.create(learning_object=learning_object, user=user)
        if _should_count(DownloadRecord, learning_object, reference):
            Interaction.objects.filter(pk=interaction.pk).update(downloaded=F('downloaded') + 1)
            interaction.refresh_from_db(fields=['downloaded'])
    return interaction
