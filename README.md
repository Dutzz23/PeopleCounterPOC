# PeopleCounter Django POC

A greenfield Django proof of concept for a Raspberry Pi style people-counting dashboard. It stores counting lines, events, daily counters, camera status, recording state, network settings, and outbound API update tasks in SQLite.

## Setup

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
python manage.py migrate
python manage.py generate_demo_data
python manage.py runserver 0.0.0.0:2001
```

Open `http://127.0.0.1:2001/` or `http://<device-ip>:2001/`.

## API

- `GET|POST /api/counting-lines/`
- `GET|PATCH|DELETE /api/counting-lines/<id>/`
- `GET|POST /api/events/`
- `GET /api/stats/daily/?date=YYYY-MM-DD`
- `GET /api/export/events/?format=csv|json`
- `GET|PATCH /api/camera-status/`
- `GET|POST /api/recording/` with `{ "action": "start" }` or `{ "action": "stop" }`
- `GET|PATCH /api/network-config/`
- `GET|POST|PATCH /api/update-tasks/`
- `GET /stream/mjpeg/`
- `GET /stream/live/`

## Detection Ingestion

Start the socket consumer:

```powershell
python manage.py consume_detections --host 127.0.0.1 --port 8765
```

Send newline-delimited JSON:

```json
{ "line_id": 1, "direction": "in", "confidence": 0.9, "track_id": "abc" }
```

The command writes `Event` rows and updates `DailyCounter` through the same service used by the REST API.

## Verification

```powershell
python manage.py test web_app
```

The initial migration seeds one default counting line. Deleting the final counting line through the API returns `409 Conflict`.

## Out of Scope

Authentication, TLS, real camera frame capture, real recording process control, and Mender packaging are intentionally left for follow-up work.
