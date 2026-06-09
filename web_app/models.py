from django.core.exceptions import ValidationError
from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models
from django.utils import timezone


class CountingLine(models.Model):
    name = models.CharField(max_length=100, unique=True)
    start_x = models.FloatField(
        validators=[MinValueValidator(0.0), MaxValueValidator(1.0)]
    )
    start_y = models.FloatField(
        validators=[MinValueValidator(0.0), MaxValueValidator(1.0)]
    )
    end_x = models.FloatField(
        validators=[MinValueValidator(0.0), MaxValueValidator(1.0)]
    )
    end_y = models.FloatField(
        validators=[MinValueValidator(0.0), MaxValueValidator(1.0)]
    )
    direction_in_label = models.CharField(max_length=50, default="in")
    direction_out_label = models.CharField(max_length=50, default="out")
    is_active = models.BooleanField(default=True)
    metadata = models.JSONField(default=dict, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["name"]

    def clean(self):
        super().clean()
        if self.start_x == self.end_x and self.start_y == self.end_y:
            raise ValidationError(
                "Counting line must have different start and end points."
            )

    def save(self, *args, **kwargs):
        self.full_clean()
        return super().save(*args, **kwargs)

    def __str__(self):
        return self.name


class Event(models.Model):
    class Direction(models.TextChoices):
        IN = "in", "In"
        OUT = "out", "Out"

    counting_line = models.ForeignKey(
        CountingLine,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="events",
    )
    line_name_snapshot = models.CharField(max_length=100, blank=True)
    direction = models.CharField(max_length=10, choices=Direction.choices)
    confidence = models.FloatField(
        default=1.0, validators=[MinValueValidator(0.0), MaxValueValidator(1.0)]
    )
    track_id = models.CharField(max_length=100, blank=True)
    metadata = models.JSONField(default=dict, blank=True)
    sent_to_api = models.BooleanField(default=False)
    occurred_at = models.DateTimeField(default=timezone.now)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-occurred_at", "-id"]
        indexes = [
            models.Index(fields=["occurred_at"]),
            models.Index(fields=["direction"]),
        ]

    def save(self, *args, **kwargs):
        if self.counting_line and not self.line_name_snapshot:
            self.line_name_snapshot = self.counting_line.name
        self.full_clean()
        return super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.direction} at {self.occurred_at:%Y-%m-%d %H:%M:%S}"


class DailyCounter(models.Model):
    date = models.DateField()
    counting_line = models.ForeignKey(
        CountingLine,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="daily_counters",
    )
    line_name_snapshot = models.CharField(max_length=100, blank=True)
    in_count = models.PositiveIntegerField(default=0)
    out_count = models.PositiveIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-date", "line_name_snapshot"]
        constraints = [
            models.UniqueConstraint(
                fields=["date", "counting_line"],
                name="unique_daily_counter_per_line",
            )
        ]

    @property
    def total(self):
        return self.in_count + self.out_count

    def __str__(self):
        return f"{self.date} {self.line_name_snapshot or 'unassigned'}"


class CameraStatus(models.Model):
    class Status(models.TextChoices):
        UNKNOWN = "unknown", "Unknown"
        ONLINE = "online", "Online"
        OFFLINE = "offline", "Offline"
        ERROR = "error", "Error"

    status = models.CharField(
        max_length=20, choices=Status.choices, default=Status.UNKNOWN
    )
    fps = models.FloatField(default=0.0, validators=[MinValueValidator(0.0)])
    resolution = models.CharField(max_length=40, blank=True)
    last_frame_at = models.DateTimeField(null=True, blank=True)
    message = models.CharField(max_length=255, blank=True)
    metadata = models.JSONField(default=dict, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-updated_at"]
        verbose_name_plural = "camera statuses"

    def __str__(self):
        return self.status


class VideoRecording(models.Model):
    class Status(models.TextChoices):
        IDLE = "idle", "Idle"
        RECORDING = "recording", "Recording"
        ERROR = "error", "Error"

    status = models.CharField(
        max_length=20, choices=Status.choices, default=Status.IDLE
    )
    started_at = models.DateTimeField(null=True, blank=True)
    stopped_at = models.DateTimeField(null=True, blank=True)
    file_path = models.CharField(max_length=255, blank=True)
    metadata = models.JSONField(default=dict, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return self.status


class APIUpdateTask(models.Model):
    class Status(models.TextChoices):
        PENDING = "pending", "Pending"
        RUNNING = "running", "Running"
        SUCCESS = "success", "Success"
        FAILED = "failed", "Failed"

    endpoint = models.CharField(max_length=255)
    status = models.CharField(
        max_length=20, choices=Status.choices, default=Status.PENDING
    )
    payload = models.JSONField(default=dict, blank=True)
    response = models.JSONField(default=dict, blank=True)
    error_message = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.endpoint} ({self.status})"


class NetworkSettings(models.Model):
    hostname = models.CharField(max_length=100, default="people-counter.local")
    interface = models.CharField(max_length=40, default="eth0")
    dhcp_enabled = models.BooleanField(default=True)
    ip_address = models.CharField(max_length=45, blank=True)
    netmask = models.CharField(max_length=45, blank=True)
    gateway = models.CharField(max_length=45, blank=True)
    dns_servers = models.JSONField(default=list, blank=True)
    metadata = models.JSONField(default=dict, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name_plural = "network settings"

    def save(self, *args, **kwargs):
        if not self.pk and NetworkSettings.objects.exists():
            self.pk = NetworkSettings.objects.first().pk
        return super().save(*args, **kwargs)

    def __str__(self):
        return self.hostname

# core/models.py
from django.db import models


class SingletonModel(models.Model):
    singleton_instance_id = 1

    class Meta:
        abstract = True

    def save(self, *args, **kwargs):
        self.pk = self.singleton_instance_id
        super().save(*args, **kwargs)

    def delete(self, *args, **kwargs):
        # Prevent deleting the singleton row
        pass

    @classmethod
    def load(cls):
        obj, _created = cls.objects.get_or_create(
            pk=cls.singleton_instance_id
        )
        return obj

class RuntimeParametrs(SingletonModel):
    # Privacy settings
    are_people_burred_in_videos = models.BooleanField(default=True)
    
    # API delivery settings
    api_delivery_url = models.URLField(blank=True)
    api_delivery_enabled = models.BooleanField(default=False)
    api_delivery_auth_token = models.CharField(max_length=255, blank=True)
    api_delivery_interval = models.IntegerField(default=60, description="in seconds")
    api_delivery_lookback_window = models.IntegerField(default=60, description="in minutes")

    # System settings
    system_timezone = models.CharField(max_length=150, default="UTC")
    store_code = models.CharField(max_length=100, blank=True)


class CountingLines(models.Model):
    @staticmethod
    def validate_points(value):
        if not isinstance(value, list):
            raise ValidationError("Points must be a list.")
        
        if len(value) < 2:
            raise ValidationError("At least 2 points are required to define a counting line.")

        for item in value:
            if not isinstance(item, dict):
                raise ValidationError("Each point must be an object.")

            if set(item.keys()) != {"x", "y"}:
                raise ValidationError("Each point must contain only x and y.")

            if not isinstance(item["x"], (int, float)):
                raise ValidationError("x must be a number.")

            if not isinstance(item["y"], (int, float)):
                raise ValidationError("y must be a number.")
            
            if item["x"] < 0.0 or item["x"] > 1.0:
                raise ValidationError("x must be between 0 and 1.")
            
            if item["y"] < 0.0 or item["y"] > 1.0:
                raise ValidationError("y must be between 0 and 1.")

    @staticmethod
    def default_points(value):
        return value or [{"x": 0.05, "y": 0.5}, {"x": 0.95, "y": 0.5}]
    
    id = models.BigAutoField(primary_key=True)
    offset = models.DecimalField(max_digits=2, decimal_places=1, default=0.1, validators=[MinValueValidator(0.0), MaxValueValidator(1.0)])
    points = models.JSONField(default=default_points, blank=True, validators=[validate_points])
    entrance_number = models.IntegerField(default=1, validators=[MinValueValidator(1)])
    in_direction_sign = models.IntegerField(
        choices=[
            (-1, "-1"),
            (1, "1"),
        ]
    )

class PleopleCountEvents(models.Model):
    id = models.BigAutoField(primary_key=True)
    counting_line = models.ForeignKey(CountingLines, on_delete=models.SET_NULL, null=True, blank=True)
    direction = models.CharField(max_length=10, choices=[("in", "in"), ("out", "out")])
    confidence = models.FloatField(default=1.0, validators=[MinValueValidator(0.0), MaxValueValidator(1.0)])
    track_id = models.CharField(max_length=100, blank=False)
    recorded_at = models.DateTimeField(auto_now_add=True)
    entrance_number = models.IntegerField(null=False)