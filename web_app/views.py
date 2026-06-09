import base64
import csv
import json
import time

from django.http import HttpResponse, StreamingHttpResponse
from django.shortcuts import render
from django.utils import timezone
from django.utils.dateparse import parse_date, parse_datetime
from rest_framework import mixins, status as drf_status, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import APIUpdateTask, CountingLine, DailyCounter, Event, VideoRecording
from .serializers import (
    APIUpdateTaskSerializer,
    CameraStatusSerializer,
    CountingLineSerializer,
    DailyCounterSerializer,
    EventSerializer,
    NetworkSettingsSerializer,
    VideoRecordingSerializer,
)
from .services import get_latest_camera_status, get_network_settings


PLACEHOLDER_JPEG_BASE64 = (
    "/9j/4AAQSkZJRgABAQAAAQABAAD/2wBDAP//////////////////////////////////////////////////////////////////////////////////////"
    "2wBDAf//////////////////////////////////////////////////////////////////////////////////////wAARCAABAAEDASIAAhEBAxEB/8QA"
    "FQABAQAAAAAAAAAAAAAAAAAAAAX/xAAUEAEAAAAAAAAAAAAAAAAAAAAA/9oADAMBAAIQAxAAAAH/xAAUEAEAAAAAAAAAAAAAAAAAAAAA/9oACAEBA"
    "AEFAqf/xAAUEQEAAAAAAAAAAAAAAAAAAAAA/9oACAEDAQE/ASP/xAAUEQEAAAAAAAAAAAAAAAAAAAAA/9oACAECAQE/ASP/xAAUEAEAAAAAAAAA"
    "AAAAAAAAAAAA/9oACAEBAAY/Al//xAAUEAEAAAAAAAAAAAAAAAAAAAAA/9oACAEBAAE/IV//2gAMAwEAAgADAAAAEP/EABQRAQAAAAAAAAAA"
    "AAAAAAAABD/2gAIAQMBAT8QH//EABQRAQAAAAAAAAAAAAAAAAAAABD/2gAIAQIBAT8QH//EABQQAQAAAAAAAAAAAAAAAAAAABD/2gAIAQEAAT8QH//Z"
)
PLACEHOLDER_JPEG = base64.b64decode(
    PLACEHOLDER_JPEG_BASE64 + "=" * (-len(PLACEHOLDER_JPEG_BASE64) % 4)
)


def dashboard_page(request):
    return render(request, "web_app/dashboard.html", {"page": "dashboard"})


def live_page(request):
    return render(request, "web_app/live.html", {"page": "live"})


def settings_page(request):
    return render(request, "web_app/settings.html", {"page": "settings"})


class CountingLineViewSet(viewsets.ModelViewSet):
    queryset = CountingLine.objects.all()
    serializer_class = CountingLineSerializer

    def destroy(self, request, *args, **kwargs):
        if self.get_queryset().count() <= 1:
            return Response(
                {"detail": "At least one counting line is required."},
                status=drf_status.HTTP_409_CONFLICT,
            )
        return super().destroy(request, *args, **kwargs)


class EventViewSet(mixins.CreateModelMixin, mixins.ListModelMixin, mixins.RetrieveModelMixin, viewsets.GenericViewSet):
    serializer_class = EventSerializer

    def get_queryset(self):
        queryset = Event.objects.select_related("counting_line").all()
        params = self.request.query_params

        direction = params.get("direction")
        if direction:
            queryset = queryset.filter(direction=direction)

        line_id = params.get("line_id")
        if line_id:
            queryset = queryset.filter(counting_line_id=line_id)

        date_value = parse_date(params.get("date") or "")
        if date_value:
            queryset = queryset.filter(occurred_at__date=date_value)

        since = parse_datetime(params.get("since") or "")
        if since:
            queryset = queryset.filter(occurred_at__gte=since)

        until = parse_datetime(params.get("until") or "")
        if until:
            queryset = queryset.filter(occurred_at__lte=until)

        return queryset


class APIUpdateTaskViewSet(viewsets.ModelViewSet):
    queryset = APIUpdateTask.objects.all()
    serializer_class = APIUpdateTaskSerializer

    @action(detail=True, methods=["post"])
    def mark_running(self, request, pk=None):
        task = self.get_object()
        task.status = APIUpdateTask.Status.RUNNING
        task.save(update_fields=["status", "updated_at"])
        return Response(self.get_serializer(task).data)


class StatsDailyView(APIView):
    def get(self, request):
        date_value = parse_date(request.query_params.get("date") or "") or timezone.localdate()
        counters = DailyCounter.objects.select_related("counting_line").filter(date=date_value)
        total_in = sum(counter.in_count for counter in counters)
        total_out = sum(counter.out_count for counter in counters)
        return Response(
            {
                "date": date_value.isoformat(),
                "total_in": total_in,
                "total_out": total_out,
                "total": total_in + total_out,
                "lines": DailyCounterSerializer(counters, many=True).data,
            }
        )


class ExportEventsView(APIView):
    def get(self, request):
        queryset = EventViewSet()
        queryset.request = request
        events = queryset.get_queryset()
        export_format = request.query_params.get("format", "json").lower()

        if export_format == "csv":
            response = HttpResponse(content_type="text/csv")
            response["Content-Disposition"] = 'attachment; filename="people-counter-events.csv"'
            writer = csv.writer(response)
            writer.writerow(["id", "occurred_at", "line_id", "line_name", "direction", "confidence", "track_id"])
            for event in events:
                writer.writerow(
                    [
                        event.id,
                        event.occurred_at.isoformat(),
                        event.counting_line_id or "",
                        event.line_name_snapshot,
                        event.direction,
                        event.confidence,
                        event.track_id,
                    ]
                )
            return response

        return Response(EventSerializer(events, many=True).data)


class CameraStatusView(APIView):
    def get(self, request):
        return Response(CameraStatusSerializer(get_latest_camera_status()).data)

    def patch(self, request):
        serializer = CameraStatusSerializer(get_latest_camera_status(), data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data)


class RecordingControlView(APIView):
    def get(self, request):
        recording = VideoRecording.objects.order_by("-created_at").first() or VideoRecording.objects.create()
        return Response(VideoRecordingSerializer(recording).data)

    def post(self, request):
        command = request.data.get("action")
        now = timezone.now()

        if command == "start":
            recording = VideoRecording.objects.filter(status=VideoRecording.Status.RECORDING).order_by("-started_at").first()
            if not recording:
                recording = VideoRecording.objects.create(status=VideoRecording.Status.RECORDING, started_at=now)
            return Response(VideoRecordingSerializer(recording).data)

        if command == "stop":
            recording = VideoRecording.objects.filter(status=VideoRecording.Status.RECORDING).order_by("-started_at").first()
            if not recording:
                return Response({"detail": "No active recording."}, status=drf_status.HTTP_409_CONFLICT)
            recording.status = VideoRecording.Status.IDLE
            recording.stopped_at = now
            recording.save(update_fields=["status", "stopped_at", "updated_at"])
            return Response(VideoRecordingSerializer(recording).data)

        return Response({"detail": "Use action 'start' or 'stop'."}, status=drf_status.HTTP_400_BAD_REQUEST)


class NetworkConfigView(APIView):
    def get(self, request):
        return Response(NetworkSettingsSerializer(get_network_settings()).data)

    def patch(self, request):
        serializer = NetworkSettingsSerializer(get_network_settings(), data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data)


def live_payload():
    today = timezone.localdate()
    counters = DailyCounter.objects.select_related("counting_line").filter(date=today)
    recent_events = Event.objects.select_related("counting_line").order_by("-occurred_at", "-id")[:10]
    total_in = sum(counter.in_count for counter in counters)
    total_out = sum(counter.out_count for counter in counters)
    return {
        "generated_at": timezone.now().isoformat(),
        "date": today.isoformat(),
        "total_in": total_in,
        "total_out": total_out,
        "total": total_in + total_out,
        "camera": CameraStatusSerializer(get_latest_camera_status()).data,
        "counters": DailyCounterSerializer(counters, many=True).data,
        "recent_events": EventSerializer(recent_events, many=True).data,
    }


def live_sse_stream(request):
    def event_stream():
        while True:
            yield f"event: update\ndata: {json.dumps(live_payload())}\n\n"
            time.sleep(2)

    response = StreamingHttpResponse(event_stream(), content_type="text/event-stream")
    response["Cache-Control"] = "no-cache"
    return response


def mjpeg_stream(request):
    def frame_stream():
        while True:
            yield b"--frame\r\nContent-Type: image/jpeg\r\n\r\n" + PLACEHOLDER_JPEG + b"\r\n"
            time.sleep(1)

    return StreamingHttpResponse(frame_stream(), content_type="multipart/x-mixed-replace; boundary=frame")
