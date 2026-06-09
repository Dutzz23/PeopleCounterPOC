from collections import defaultdict
from datetime import timedelta
import logging

import requests
from celery import shared_task
from django.utils import timezone

from .models import RuntimeParametrs, AppStatuses, PleopleCountEvents

logger = logging.getLogger(__name__)


@shared_task(
    bind=True,
    autoretry_for=(requests.RequestException,),
    retry_backoff=True,
    retry_kwargs={"max_retries": 3},
)
def deliver_people_count_events(self):
    params = RuntimeParametrs.load()
    statuses = AppStatuses.load()

    now = timezone.now()

    statuses.last_api_delivery_attempt = now
    statuses.save(update_fields=["last_api_delivery_attempt"])

    if not params.api_delivery_enabled:
        logger.info("API delivery skipped: disabled")
        return {
            "status": "skipped",
            "reason": "api_delivery_enabled is False",
        }

    if not params.api_delivery_url:
        logger.warning("API delivery skipped: api_delivery_url is empty")
        return {
            "status": "skipped",
            "reason": "api_delivery_url is empty",
        }

    window_end = now
    window_start = window_end - timedelta(
        minutes=params.api_delivery_lookback_window
    )

    events = list(
        PleopleCountEvents.objects.filter(
            recorded_at__gte=window_start,
            recorded_at__lt=window_end,
        )
        .select_related("counting_line")
        .order_by("entrance_number", "recorded_at")
    )

    events_by_entrance = defaultdict(list)

    for event in events:
        events_by_entrance[event.entrance_number].append(event)

    headers = {
        "Content-Type": "application/json",
    }

    if params.api_delivery_auth_token:
        headers["Authorization"] = f"Bearer {params.api_delivery_auth_token}"

    posts_sent = 0
    total_events_sent = 0

    for entrance_number, entrance_events in events_by_entrance.items():
        payload = {
            "store_code": params.store_code,
            "timezone": params.system_timezone,
            "entrance_number": entrance_number,
            "window": {
                "from": window_start.isoformat(),
                "to": window_end.isoformat(),
            },
            "events": [
                {
                    "id": event.id,
                    "direction": event.direction,
                    "confidence": event.confidence,
                    "tracklet_id": event.tracklet_id,
                    "entrance_number": event.entrance_number,
                    "recorded_at": event.recorded_at.isoformat(),
                    "counting_line": (
                        {
                            "id": event.counting_line.id,
                            "offset": str(event.counting_line.offset),
                            "points": event.counting_line.points,
                            "entrance_number": event.counting_line.entrance_number,
                            "in_direction_sign": event.counting_line.in_direction_sign,
                        }
                        if event.counting_line is not None
                        else None
                    ),
                }
                for event in entrance_events
            ],
        }

        logger.info(
            "Sending %s people count events for entrance %s to API",
            len(entrance_events),
            entrance_number,
        )

        response = requests.post(
            params.api_delivery_url,
            json=payload,
            headers=headers,
            timeout=10,
        )

        response.raise_for_status()

        posts_sent += 1
        total_events_sent += len(entrance_events)

        logger.info(
            "Successfully sent people count events for entrance %s. Status code: %s",
            entrance_number,
            response.status_code,
        )

    statuses.last_api_delivery_success = timezone.now()
    statuses.save(update_fields=["last_api_delivery_success"])

    return {
        "status": "success",
        "posts_sent": posts_sent,
        "events_sent": total_events_sent,
        "window_start": window_start.isoformat(),
        "window_end": window_end.isoformat(),
    }