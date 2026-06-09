from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .views import (
    APIUpdateTaskViewSet,
    CameraStatusView,
    CountingLineViewSet,
    EventViewSet,
    ExportEventsView,
    NetworkConfigView,
    RecordingControlView,
    StatsDailyView,
    dashboard_page,
    live_page,
    live_sse_stream,
    mjpeg_stream,
    settings_page,
)

router = DefaultRouter()
router.register("counting-lines", CountingLineViewSet, basename="counting-line")
router.register("events", EventViewSet, basename="event")
router.register("update-tasks", APIUpdateTaskViewSet, basename="update-task")

urlpatterns = [
    path("", dashboard_page, name="dashboard"),
    path("live/", live_page, name="live"),
    path("settings/", settings_page, name="settings"),
    path("api/stats/daily/", StatsDailyView.as_view(), name="stats-daily"),
    path("api/export/events/", ExportEventsView.as_view(), name="export-events"),
    path("api/camera-status/", CameraStatusView.as_view(), name="camera-status"),
    path("api/recording/", RecordingControlView.as_view(), name="recording-control"),
    path("api/network-config/", NetworkConfigView.as_view(), name="network-config"),
    path("api/", include(router.urls)),
    path("stream/mjpeg/", mjpeg_stream, name="mjpeg-stream"),
    path("stream/live/", live_sse_stream, name="live-sse-stream"),
]
