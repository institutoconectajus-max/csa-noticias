import os, requests
from http.server import BaseHTTPRequestHandler

CATEGORIES = ["procuradoria", "magistratura", "promotoria", "defensoria", "delegado"]
BASE_URL   = os.environ.get("VERCEL_URL", "csa-noticias.vercel.app")

class handler(BaseHTTPRequestHandler):
    def do_GET(self):
        # Verifica se é chamada legítima do Vercel Cron
        auth = self.headers.get("authorization", "")
        cron_secret = os.environ.get("CRON_SECRET", "")
        if cron_secret and auth != f"Bearer {cron_secret}":
            self.send_response(401)
            self.end_headers()
            return

        results = {}
        for cat in CATEGORIES:
            try:
                r = requests.get(
                    f"https://{BASE_URL}/api/{cat}",
                    headers={"Cache-Control": "no-cache"},
                    timeout=30
                )
                results[cat] = r.status_code
            except Exception as e:
                results[cat] = str(e)

        import json
        data = json.dumps({"status": "ok", "results": results}).encode()
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.end_headers()
        self.wfile.write(data)
