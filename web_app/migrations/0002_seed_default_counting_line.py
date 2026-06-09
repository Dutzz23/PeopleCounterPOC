from django.db import migrations


def seed_default_counting_line(apps, schema_editor):
    CountingLine = apps.get_model("web_app", "CountingLine")
    CountingLine.objects.get_or_create(
        name="Main entrance",
        defaults={
            "start_x": 0.2,
            "start_y": 0.5,
            "end_x": 0.8,
            "end_y": 0.5,
            "direction_in_label": "in",
            "direction_out_label": "out",
            "is_active": True,
            "metadata": {"seeded": True},
        },
    )


class Migration(migrations.Migration):
    dependencies = [
        ("web_app", "0001_initial"),
    ]

    operations = [
        migrations.RunPython(seed_default_counting_line, migrations.RunPython.noop),
    ]
