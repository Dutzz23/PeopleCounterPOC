import json
import socketserver

from django.core.management.base import BaseCommand
from django.utils.dateparse import parse_datetime

from web_app.models import CountingLine
from web_app.services import record_event


class ReusableThreadingTCPServer(socketserver.ThreadingTCPServer):
    allow_reuse_address = True


class Command(BaseCommand):
    help = "Listen for newline-delimited JSON detection events and write them to the database."

    def add_arguments(self, parser):
        parser.add_argument("--host", default="127.0.0.1", help="Host/IP to bind.")
        parser.add_argument("--port", type=int, default=8765, help="TCP port to bind.")

    def handle(self, *args, **options):
        command = self

        class DetectionHandler(socketserver.StreamRequestHandler):
            def handle(self):
                for raw_line in self.rfile:
                    try:
                        payload = json.loads(raw_line.decode("utf-8"))
                        occurred_at = parse_datetime(payload.get("occurred_at") or "")
                        event = record_event(
                            line_id=payload.get("line_id") or payload.get("counting_line"),
                            direction=payload["direction"],
                            confidence=float(payload.get("confidence", 1.0)),
                            track_id=str(payload.get("track_id", "")),
                            metadata=payload.get("metadata") or {},
                            occurred_at=occurred_at,
                            sent_to_api=bool(payload.get("sent_to_api", False)),
                        )
                        command.stdout.write(f"recorded event {event.id}")
                    except CountingLine.DoesNotExist:
                        command.stderr.write(f"unknown counting line: {payload.get('line_id')}")
                    except Exception as exc:
                        command.stderr.write(f"invalid detection payload: {exc}")

        address = (options["host"], options["port"])
        self.stdout.write(f"Listening for detections on {address[0]}:{address[1]}")
        try:
            with ReusableThreadingTCPServer(address, DetectionHandler) as server:
                server.serve_forever()
        except KeyboardInterrupt:
            self.stdout.write("Stopped detection consumer.")
