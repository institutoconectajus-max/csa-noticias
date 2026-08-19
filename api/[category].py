"""
Vercel Serverless Function — /api/[category]
Ex: /api/procuradoria, /api/magistratura, etc.
"""

import time
import json
import requests
from bs4 import BeautifulSoup
from http.server import BaseHTTPRequestHandler

CATEGORIES = {
    "procuradoria": "https://cj.estrategia.com/portal/procuradoria/",
    "magistratura": "https://cj.estrategia.com/portal/magistratura/",
    "promotoria":   "https://cj.estrategia.com/portal/promotoria/",
    "defensoria":   "https://cj.estrategia.com/portal/defensoria/",
    "delegado":     "https://cj.estrategia.com/portal/delegado/",
}

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/125.0.0.0 Safari/537.36"
    )
}

_cache: dict = {}
CACHE_TTL = 3600


def fetch_articles(category: str, limit: int = 12):
    now = time.time()
    cached = _cache.get(category)
    if cached and (now - cached[0]) < CACHE_TTL:
        return cached[1][:limit]

    url = CATEGORIES[category]
    try:
        resp = requests.get(url, headers=HEADERS, timeout=10)
        resp.raise_for_status()
    except Exception:
        return _cache[category][1][:limit] if category in _cache else []

    soup = BeautifulSoup(resp.content, "html.parser")
    articles = []

    for item in soup.select("article"):
        if len(articles) >= 12:
            break
        title_el = item.select_one(".entry-title a, h2 a, h3 a")
        if not title_el:
            continue
        title = title_el.get_text(strip=True)
        link  = title_el.get("href", "")
        if not title or not link:
            continue

        date_el    = item.select_one("time.entry-date, .entry-date, time")
        img_el     = item.select_one("img")
        excerpt_el = item.select_one(".entry-summary p, .entry-content p")

        articles.append({
            "title":   title,
            "link":    link,
            "date":    date_el.get_text(strip=True) if date_el else "",
            "thumb":   (img_el.get("src") or img_el.get("data-src") or "") if img_el else "",
            "excerpt": excerpt_el.get_text(strip=True)[:160] if excerpt_el else "",
        })

    _cache[category] = (now, articles)
    return articles[:limit]


def respond(handler, status, body):
    data = json.dumps(body, ensure_ascii=False).encode("utf-8")
    handler.send_response(status)
    handler.send_header("Content-Type", "application/json; charset=utf-8")
    handler.send_header("Access-Control-Allow-Origin", "*")
    handler.send_header("Cache-Control", "s-maxage=3600, stale-while-revalidate=86400")
    handler.end_headers()
    handler.wfile.write(data)


class handler(BaseHTTPRequestHandler):

    def do_GET(self):
        # Extrai categoria do path: /api/procuradoria → procuradoria
        category = self.path.rstrip("/").split("/")[-1].split("?")[0]

        if category not in CATEGORIES:
            respond(self, 404, {
                "error": f"Categoria '{category}' não encontrada.",
                "available": list(CATEGORIES.keys()),
            })
            return

        articles = fetch_articles(category)
        respond(self, 200, {
            "category": category,
            "source":   CATEGORIES[category],
            "count":    len(articles),
            "articles": articles,
        })

    def do_OPTIONS(self):
        self.send_response(200)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, OPTIONS")
        self.end_headers()
