from datetime import timedelta

from django.core.management.base import BaseCommand
from django.utils import timezone

from web_app.models import CameraStatus, CountingLine, NetworkSettings
from web_app.services import record_event


class Command(BaseCommand):
    help = "Create sample camera status and people-counting events."

    def add_arguments(self, parser):
        parser.add_argument("--events", type=int, default=12, help="Number of demo events to create.")

    def handle(self, *args, **options):
        line, _ = CountingLine.objects.get_or_create(
            name="Main entrance",
            defaults={
                "start_x": 0.2,
                "start_y": 0.5,
                "end_x": 0.8,
                "end_y": 0.5,
            },
        )

        CameraStatus.objects.create(
            status=CameraStatus.Status.ONLINE,
            fps=24.0,
            resolution="1280x720",
            last_frame_at=timezone.now(),
            message="demo stream",
        )
        NetworkSettings.objects.get_or_create(hostname="people-counter.local")

        total = max(options["events"], 0)
        for index in range(total):
            direction = "in" if index % 3 != 0 else "out"
            record_event(
                counting_line=line,
                direction=direction,
                confidence=0.82 + (index % 5) * 0.03,
                track_id=f"demo-{index + 1}",
                metadata={"source": "demo"},
                occurred_at=timezone.now() - timedelta(minutes=total - index),
            )

        self.stdout.write(self.style.SUCCESS(f"Generated {total} demo events."))
