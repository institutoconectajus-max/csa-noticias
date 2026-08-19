"""
Vercel Serverless Function — /api
Retorna status e endpoints disponíveis.
"""

import json
from http.server import BaseHTTPRequestHandler


class handler(BaseHTTPRequestHandler):

    def do_GET(self):
        self.send_response(200)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Access-Control-Allow-Origin", "*")
        self.end_headers()
        self.wfile.write(json.dumps({
            "status": "ok",
            "message": "CSA Notícias API — online",
            "endpoints": [
                "/api/noticias/procuradoria",
                "/api/noticias/magistratura",
                "/api/noticias/promotoria",
                "/api/noticias/defensoria",
                "/api/noticias/delegado",
            ],
        }, ensure_ascii=False).encode("utf-8"))
