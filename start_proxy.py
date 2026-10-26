import json
from http.server import HTTPServer, SimpleHTTPRequestHandler
import os

class SanitizedFeedHandler(SimpleHTTPRequestHandler):
    def do_GET(self):
        if self.path == '/status':
            try:
                with open(r'C:\Users\Joshu\AppData\Local\MylesAI\status_feed_sample.json', 'r') as f:
                    data = json.load(f)
                self.send_response(200)
                self.send_header('Content-type', 'application/json')
                self.end_headers()
                self.wfile.write(json.dumps(data).encode())
            except Exception as e:
                self.send_error(500, str(e))
        else:
            self.send_response(404)
            self.end_headers()

if __name__ == '__main__':
    server = HTTPServer(('127.0.0.1', 8080), SanitizedFeedHandler)
    print('Local Proxy Active: http://127.0.0.1:8080/status')
    server.serve_forever()