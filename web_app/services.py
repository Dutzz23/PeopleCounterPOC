from django.db import transaction
from django.utils import timezone

from .models import CameraStatus, CountingLine, DailyCounter, Event, NetworkSettings


def local_date_for(value):
    if timezone.is_aware(value):
        return timezone.localtime(value).date()
    return value.date()


@transaction.atomic
def record_event(
    *,
    direction,
    counting_line=None,
    line_id=None,
    confidence=1.0,
    track_id="",
    metadata=None,
    occurred_at=None,
    sent_to_api=False,
):
    if line_id is not None and counting_line is None:
        counting_line = CountingLine.objects.get(pk=line_id)

    occurred_at = occurred_at or timezone.now()
    metadata = metadata or {}
    line_name_snapshot = counting_line.name if counting_line else ""

    event = Event.objects.create(
        counting_line=counting_line,
        line_name_snapshot=line_name_snapshot,
        direction=direction,
        confidence=confidence,
        track_id=track_id,
        metadata=metadata,
        occurred_at=occurred_at,
        sent_to_api=sent_to_api,
    )

    counter, _ = DailyCounter.objects.select_for_update().get_or_create(
        date=local_date_for(event.occurred_at),
        counting_line=counting_line,
        defaults={"line_name_snapshot": line_name_snapshot},
    )
    if line_name_snapshot and counter.line_name_snapshot != line_name_snapshot:
        counter.line_name_snapshot = line_name_snapshot

    if direction == Event.Direction.IN:
        counter.in_count += 1
    else:
        counter.out_count += 1

    counter.save(update_fields=["line_name_snapshot", "in_count", "out_count", "updated_at"])
    return event


def get_latest_camera_status():
    return CameraStatus.objects.order_by("-updated_at", "-id").first() or CameraStatus.objects.create()


def get_network_settings():
    return NetworkSettings.objects.first() or NetworkSettings.objects.create()
