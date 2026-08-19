import time, json, requests
from bs4 import BeautifulSoup
from http.server import BaseHTTPRequestHandler

CATEGORY = "defensoria"
URL = "https://cj.estrategia.com/portal/defensoria/"
HEADERS = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36"}
_cache = {}
CACHE_TTL = 3600

def fetch_articles(limit=12):
    now = time.time()
    cached = _cache.get(CATEGORY)
    if cached and (now - cached[0]) < CACHE_TTL:
        return cached[1][:limit]
    try:
        resp = requests.get(URL, headers=HEADERS, timeout=10)
        resp.raise_for_status()
    except Exception:
        return _cache[CATEGORY][1][:limit] if CATEGORY in _cache else []
    soup = BeautifulSoup(resp.content, "html.parser")
    articles = []
    for item in soup.select("article"):
        if len(articles) >= 12: break
        title_el = item.select_one(".entry-title a")
        if not title_el: continue
        title = title_el.get_text(strip=True)
        if not title: continue
        date_el = item.select_one(".meta-date")
        date = date_el.get_text(strip=True) if date_el else ""
        date = date.replace("Publicado em ", "").replace("Atualizado em ", "")
        articles.append({"title": title, "date": date})
    _cache[CATEGORY] = (now, articles)
    return articles[:limit]

class handler(BaseHTTPRequestHandler):
    def do_GET(self):
        articles = fetch_articles()
        data = json.dumps({"category": CATEGORY, "count": len(articles), "articles": articles}, ensure_ascii=False).encode("utf-8")
        self.send_response(200)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Cache-Control", "s-maxage=3600, stale-while-revalidate=86400")
        self.end_headers()
        self.wfile.write(data)
    def do_OPTIONS(self):
        self.send_response(200)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.end_headers()
