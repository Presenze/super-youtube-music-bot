#!/usr/bin/env python3
"""
Healthcheck endpoint for Railway
"""

from http.server import HTTPServer, BaseHTTPRequestHandler
import threading
import os

class HealthCheckHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        if self.path == '/health':
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            self.wfile.write(b'{"status": "ok", "service": "gigliotube-bot"}')
        else:
            self.send_response(404)
            self.end_headers()

def start_healthcheck_server():
    """Avvia server di healthcheck"""
    port = int(os.getenv('PORT', 8080))
    server = HTTPServer(('0.0.0.0', port), HealthCheckHandler)
    print(f"🏥 Healthcheck server started on port {port}")
    server.serve_forever()

if __name__ == "__main__":
    start_healthcheck_server()
