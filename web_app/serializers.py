from rest_framework import serializers

from .models import (
    APIUpdateTask,
    CameraStatus,
    CountingLine,
    DailyCounter,
    Event,
    NetworkSettings,
    VideoRecording,
)
from .services import record_event


class CountingLineSerializer(serializers.ModelSerializer):
    class Meta:
        model = CountingLine
        fields = [
            "id",
            "name",
            "start_x",
            "start_y",
            "end_x",
            "end_y",
            "direction_in_label",
            "direction_out_label",
            "is_active",
            "metadata",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "created_at", "updated_at"]

    def validate(self, attrs):
        values = {
            field: attrs.get(field, getattr(self.instance, field, None))
            for field in ("start_x", "start_y", "end_x", "end_y")
        }
        if values["start_x"] == values["end_x"] and values["start_y"] == values["end_y"]:
            raise serializers.ValidationError("Counting line must have different start and end points.")
        return attrs


class EventSerializer(serializers.ModelSerializer):
    counting_line_name = serializers.SerializerMethodField()

    class Meta:
        model = Event
        fields = [
            "id",
            "counting_line",
            "counting_line_name",
            "line_name_snapshot",
            "direction",
            "confidence",
            "track_id",
            "metadata",
            "sent_to_api",
            "occurred_at",
            "created_at",
        ]
        read_only_fields = ["id", "counting_line_name", "line_name_snapshot", "created_at"]

    def get_counting_line_name(self, obj):
        return obj.line_name_snapshot or (obj.counting_line.name if obj.counting_line else "")

    def create(self, validated_data):
        return record_event(**validated_data)


class DailyCounterSerializer(serializers.ModelSerializer):
    counting_line_name = serializers.SerializerMethodField()
    total = serializers.IntegerField(read_only=True)

    class Meta:
        model = DailyCounter
        fields = [
            "id",
            "date",
            "counting_line",
            "counting_line_name",
            "line_name_snapshot",
            "in_count",
            "out_count",
            "total",
            "updated_at",
        ]
        read_only_fields = fields

    def get_counting_line_name(self, obj):
        return obj.line_name_snapshot or (obj.counting_line.name if obj.counting_line else "")


class CameraStatusSerializer(serializers.ModelSerializer):
    class Meta:
        model = CameraStatus
        fields = [
            "id",
            "status",
            "fps",
            "resolution",
            "last_frame_at",
            "message",
            "metadata",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "created_at", "updated_at"]


class VideoRecordingSerializer(serializers.ModelSerializer):
    class Meta:
        model = VideoRecording
        fields = [
            "id",
            "status",
            "started_at",
            "stopped_at",
            "file_path",
            "metadata",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "created_at", "updated_at"]


class APIUpdateTaskSerializer(serializers.ModelSerializer):
    class Meta:
        model = APIUpdateTask
        fields = [
            "id",
            "endpoint",
            "status",
            "payload",
            "response",
            "error_message",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "created_at", "updated_at"]


class NetworkSettingsSerializer(serializers.ModelSerializer):
    class Meta:
        model = NetworkSettings
        fields = [
            "id",
            "hostname",
            "interface",
            "dhcp_enabled",
            "ip_address",
            "netmask",
            "gateway",
            "dns_servers",
            "metadata",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "created_at", "updated_at"]
