import os, json
from http.server import BaseHTTPRequestHandler

class handler(BaseHTTPRequestHandler):
    def do_GET(self):
        key = os.environ.get("GEMINI_API_KEY", "NAO_ENCONTRADA")
        data = json.dumps({
            "gemini_key_present": key != "NAO_ENCONTRADA",
            "gemini_key_prefix": key[:8] if key != "NAO_ENCONTRADA" else "ausente"
        }).encode()
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.send_header("Access-Control-Allow-Origin", "*")
        self.end_headers()
        self.wfile.write(data)
