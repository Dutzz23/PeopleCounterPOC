import django.core.validators
import django.db.models.deletion
import django.utils.timezone
from django.db import migrations, models


class Migration(migrations.Migration):
    initial = True

    dependencies = []

    operations = [
        migrations.CreateModel(
            name="APIUpdateTask",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("endpoint", models.CharField(max_length=255)),
                ("status", models.CharField(choices=[("pending", "Pending"), ("running", "Running"), ("success", "Success"), ("failed", "Failed")], default="pending", max_length=20)),
                ("payload", models.JSONField(blank=True, default=dict)),
                ("response", models.JSONField(blank=True, default=dict)),
                ("error_message", models.TextField(blank=True)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
            ],
            options={"ordering": ["-created_at"]},
        ),
        migrations.CreateModel(
            name="CameraStatus",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("status", models.CharField(choices=[("unknown", "Unknown"), ("online", "Online"), ("offline", "Offline"), ("error", "Error")], default="unknown", max_length=20)),
                ("fps", models.FloatField(default=0.0, validators=[django.core.validators.MinValueValidator(0.0)])),
                ("resolution", models.CharField(blank=True, max_length=40)),
                ("last_frame_at", models.DateTimeField(blank=True, null=True)),
                ("message", models.CharField(blank=True, max_length=255)),
                ("metadata", models.JSONField(blank=True, default=dict)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
            ],
            options={"verbose_name_plural": "camera statuses", "ordering": ["-updated_at"]},
        ),
        migrations.CreateModel(
            name="CountingLine",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("name", models.CharField(max_length=100, unique=True)),
                ("start_x", models.FloatField(validators=[django.core.validators.MinValueValidator(0.0), django.core.validators.MaxValueValidator(1.0)])),
                ("start_y", models.FloatField(validators=[django.core.validators.MinValueValidator(0.0), django.core.validators.MaxValueValidator(1.0)])),
                ("end_x", models.FloatField(validators=[django.core.validators.MinValueValidator(0.0), django.core.validators.MaxValueValidator(1.0)])),
                ("end_y", models.FloatField(validators=[django.core.validators.MinValueValidator(0.0), django.core.validators.MaxValueValidator(1.0)])),
                ("direction_in_label", models.CharField(default="in", max_length=50)),
                ("direction_out_label", models.CharField(default="out", max_length=50)),
                ("is_active", models.BooleanField(default=True)),
                ("metadata", models.JSONField(blank=True, default=dict)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
            ],
            options={"ordering": ["name"]},
        ),
        migrations.CreateModel(
            name="NetworkSettings",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("hostname", models.CharField(default="people-counter.local", max_length=100)),
                ("interface", models.CharField(default="eth0", max_length=40)),
                ("dhcp_enabled", models.BooleanField(default=True)),
                ("ip_address", models.CharField(blank=True, max_length=45)),
                ("netmask", models.CharField(blank=True, max_length=45)),
                ("gateway", models.CharField(blank=True, max_length=45)),
                ("dns_servers", models.JSONField(blank=True, default=list)),
                ("metadata", models.JSONField(blank=True, default=dict)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
            ],
            options={"verbose_name_plural": "network settings"},
        ),
        migrations.CreateModel(
            name="VideoRecording",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("status", models.CharField(choices=[("idle", "Idle"), ("recording", "Recording"), ("error", "Error")], default="idle", max_length=20)),
                ("started_at", models.DateTimeField(blank=True, null=True)),
                ("stopped_at", models.DateTimeField(blank=True, null=True)),
                ("file_path", models.CharField(blank=True, max_length=255)),
                ("metadata", models.JSONField(blank=True, default=dict)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
            ],
            options={"ordering": ["-created_at"]},
        ),
        migrations.CreateModel(
            name="Event",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("line_name_snapshot", models.CharField(blank=True, max_length=100)),
                ("direction", models.CharField(choices=[("in", "In"), ("out", "Out")], max_length=10)),
                ("confidence", models.FloatField(default=1.0, validators=[django.core.validators.MinValueValidator(0.0), django.core.validators.MaxValueValidator(1.0)])),
                ("track_id", models.CharField(blank=True, max_length=100)),
                ("metadata", models.JSONField(blank=True, default=dict)),
                ("sent_to_api", models.BooleanField(default=False)),
                ("occurred_at", models.DateTimeField(default=django.utils.timezone.now)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("counting_line", models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name="events", to="web_app.countingline")),
            ],
            options={"ordering": ["-occurred_at", "-id"], "indexes": [models.Index(fields=["occurred_at"], name="web_app_eve_occurre_84107a_idx"), models.Index(fields=["direction"], name="web_app_eve_directi_51ce8f_idx")]},
        ),
        migrations.CreateModel(
            name="DailyCounter",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("date", models.DateField()),
                ("line_name_snapshot", models.CharField(blank=True, max_length=100)),
                ("in_count", models.PositiveIntegerField(default=0)),
                ("out_count", models.PositiveIntegerField(default=0)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                ("counting_line", models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name="daily_counters", to="web_app.countingline")),
            ],
            options={"ordering": ["-date", "line_name_snapshot"], "constraints": [models.UniqueConstraint(fields=("date", "counting_line"), name="unique_daily_counter_per_line")]},
        ),
    ]
