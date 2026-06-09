import json

from django.core.exceptions import ValidationError
from django.test import TestCase
from django.utils import timezone

from .models import CountingLine, DailyCounter
from .services import record_event


class CountingLineValidationTests(TestCase):
    def test_coordinates_must_be_normalized(self):
        line = CountingLine(
            name="Bad line",
            start_x=1.2,
            start_y=0.5,
            end_x=0.8,
            end_y=0.5,
        )

        with self.assertRaises(ValidationError):
            line.full_clean()

    def test_line_must_have_length(self):
        line = CountingLine(
            name="Zero line",
            start_x=0.5,
            start_y=0.5,
            end_x=0.5,
            end_y=0.5,
        )

        with self.assertRaises(ValidationError):
            line.full_clean()


class PeopleCounterAPITests(TestCase):
    def setUp(self):
        self.line = CountingLine.objects.first()

    def test_delete_last_counting_line_is_blocked(self):
        CountingLine.objects.exclude(pk=self.line.pk).delete()

        response = self.client.delete(f"/api/counting-lines/{self.line.pk}/")

        self.assertEqual(response.status_code, 409)
        self.assertTrue(CountingLine.objects.filter(pk=self.line.pk).exists())

    def test_event_creation_increments_daily_counter(self):
        payload = {
            "counting_line": self.line.pk,
            "direction": "in",
            "confidence": 0.93,
            "track_id": "track-1",
        }

        response = self.client.post(
            "/api/events/",
            data=json.dumps(payload),
            content_type="application/json",
        )

        self.assertEqual(response.status_code, 201)
        counter = DailyCounter.objects.get(date=timezone.localdate(), counting_line=self.line)
        self.assertEqual(counter.in_count, 1)
        self.assertEqual(counter.out_count, 0)

    def test_stats_and_csv_export(self):
        record_event(counting_line=self.line, direction="in", confidence=0.9, track_id="a")
        record_event(counting_line=self.line, direction="out", confidence=0.8, track_id="b")
        today = timezone.localdate().isoformat()

        stats = self.client.get(f"/api/stats/daily/?date={today}")
        self.assertEqual(stats.status_code, 200)
        self.assertEqual(stats.json()["total_in"], 1)
        self.assertEqual(stats.json()["total_out"], 1)

        export = self.client.get("/api/export/events/?format=csv")
        self.assertEqual(export.status_code, 200)
        self.assertIn("text/csv", export["Content-Type"])
        self.assertIn("track_id", export.content.decode("utf-8"))

    def test_streaming_endpoints_smoke(self):
        mjpeg = self.client.get("/stream/mjpeg/")
        self.assertEqual(mjpeg.status_code, 200)
        self.assertTrue(mjpeg.streaming)
        self.assertIn("multipart/x-mixed-replace", mjpeg["Content-Type"])

        sse = self.client.get("/stream/live/")
        self.assertEqual(sse.status_code, 200)
        self.assertTrue(sse.streaming)
        self.assertIn("text/event-stream", sse["Content-Type"])
