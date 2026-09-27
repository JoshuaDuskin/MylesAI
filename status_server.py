import json
import time
from http.server import HTTPServer, BaseHTTPRequestHandler
import psutil


class StatusHandler(BaseHTTPRequestHandler):
    def log_message(self, format, *args):
        pass  # Suppress default logging

    def do_GET(self):
        self.send_response(200)
        self.send_header('Content-Type', 'application/json')
        self.end_headers()

        cpu_percent = psutil.cpu_percent(interval=None)
        memory = psutil.virtual_memory()
        disk = psutil.disk_usage('/')

        status_data = {
            "timestamp": time.time(),
            "cpu_percent": cpu_percent,
            "memory": {
                "total": memory.total,
                "available": memory.available,
                "percent": memory.percent
            },
            "disk": {
                "total": disk.total,
                "used": disk.used,
                "free": disk.free,
                "percent": disk.percent
            }
        }

        self.wfile.write(json.dumps(status_data).encode())


if __name__ == '__main__':
    server = HTTPServer(('localhost', 8080), StatusHandler)
    print("Status server running on http://localhost:8080")
    server.serve_forever()