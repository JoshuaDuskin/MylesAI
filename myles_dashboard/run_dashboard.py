import http.server
import json
import threading
import time
from datetime import datetime

class StatusSimulator:
    def __init__(self):
        self.last_update = datetime.now()
        self.latency_ms = 42
        self.status = 'connected'
        self.running = True

    def update(self):
        self.last_update = datetime.now()
        self.latency_ms = round(30 + (time.time_ns() % 1000) / 1_000_000, 2)
        # Randomly simulate occasional disconnection for realism
        if time.time() - self.last_update.timestamp() > 5:
            self.status = 'disconnected'
        else:
            self.status = 'connected'

    def get_data(self):
        return {
            "status": self.status,
            "latency_ms": self.latency_ms,
            "last_update": self.last_update.isoformat()
        }

simulator = StatusSimulator()
update_thread = threading.Thread(target=simulator.update, daemon=True)
update_thread.start()

class MylesHandler(http.server.SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory='.', **kwargs)
    
    def do_GET(self):
        if self.path == '/api/status':
            self.send_response(200)
            self.send_header('Content-Type', 'application/json')
            self.send_header('Cache-Control', 'no-cache')
            self.end_headers()
            data = json.dumps(simulator.get_data())
            self.wfile.write(data.encode('utf-8'))
        elif self.path == '/':
            # Serve index.html from current directory
            try:
                with open('index.html', 'rb') as f:
                    content = f.read()
                self.send_response(200)
                self.send_header('Content-Type', 'text/html')
                self.end_headers()
                self.wfile.write(content)
            except FileNotFoundError:
                self.send_error(404, "File not found")
        else:
            super().do_GET()

    def do_POST(self):
        if self.path == '/api/status':
            self.send_response(200)
            self.send_header('Content-Type', 'application/json')
            self.end_headers()
            data = json.dumps(simulator.get_data())
            self.wfile.write(data.encode('utf-8'))
        else:
            super().do_POST()

if __name__ == '__main__':
    print("Starting Myles Dashboard Server on http://127.0.0.1:8080")
    server = http.server.HTTPServer(('127.0.0.1', 8080), MylesHandler)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nShutting down server...")
        server.shutdown()