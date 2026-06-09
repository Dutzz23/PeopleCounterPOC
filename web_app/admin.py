from django.contrib import admin

from .models import (
    APIUpdateTask,
    CameraStatus,
    CountingLine,
    DailyCounter,
    Event,
    NetworkSettings,
    VideoRecording,
)


@admin.register(CountingLine)
class CountingLineAdmin(admin.ModelAdmin):
    list_display = ("name", "is_active", "start_x", "start_y", "end_x", "end_y", "updated_at")
    list_filter = ("is_active",)
    search_fields = ("name",)


@admin.register(Event)
class EventAdmin(admin.ModelAdmin):
    list_display = ("occurred_at", "direction", "line_name_snapshot", "confidence", "track_id", "sent_to_api")
    list_filter = ("direction", "sent_to_api", "occurred_at")
    search_fields = ("line_name_snapshot", "track_id")


@admin.register(DailyCounter)
class DailyCounterAdmin(admin.ModelAdmin):
    list_display = ("date", "line_name_snapshot", "in_count", "out_count", "total", "updated_at")
    list_filter = ("date",)
    search_fields = ("line_name_snapshot",)


@admin.register(CameraStatus)
class CameraStatusAdmin(admin.ModelAdmin):
    list_display = ("status", "fps", "resolution", "last_frame_at", "updated_at")


@admin.register(VideoRecording)
class VideoRecordingAdmin(admin.ModelAdmin):
    list_display = ("status", "started_at", "stopped_at", "file_path", "updated_at")
    list_filter = ("status",)


@admin.register(APIUpdateTask)
class APIUpdateTaskAdmin(admin.ModelAdmin):
    list_display = ("endpoint", "status", "created_at", "updated_at")
    list_filter = ("status",)
    search_fields = ("endpoint", "error_message")


@admin.register(NetworkSettings)
class NetworkSettingsAdmin(admin.ModelAdmin):
    list_display = ("hostname", "interface", "dhcp_enabled", "ip_address", "updated_at")
