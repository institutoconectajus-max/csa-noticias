import time, json, requests
from bs4 import BeautifulSoup
from http.server import BaseHTTPRequestHandler

CATEGORY = "delegado"
URL = "https://cj.estrategia.com/portal/delegado/"
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
        title_el = item.select_one(".entry-title a, h2 a, h3 a")
        if not title_el: continue
        title = title_el.get_text(strip=True)
        link  = title_el.get("href", "")
        if not title or not link: continue
        date_el    = item.select_one("time.entry-date, .entry-date, time")
        img_el     = item.select_one("img")
        excerpt_el = item.select_one(".entry-summary p, .entry-content p")
        articles.append({
            "title":   title, "link": link,
            "date":    date_el.get_text(strip=True) if date_el else "",
            "thumb":   (img_el.get("src") or img_el.get("data-src") or "") if img_el else "",
            "excerpt": excerpt_el.get_text(strip=True)[:160] if excerpt_el else "",
        })
    _cache[CATEGORY] = (now, articles)
    return articles[:limit]

class handler(BaseHTTPRequestHandler):
    def do_GET(self):
        articles = fetch_articles()
        data = json.dumps({"category": CATEGORY, "source": URL, "count": len(articles), "articles": articles}, ensure_ascii=False).encode("utf-8")
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
