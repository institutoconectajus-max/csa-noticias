import time, json, requests
import xml.etree.ElementTree as ET
from http.server import BaseHTTPRequestHandler

CATEGORY = "delegado"
LABEL    = "Delegado"
CACHE_TTL = 3600
_cache = {}

FEEDS = [
    ("Estratégia Carreiras Jurídicas", "https://cj.estrategia.com/portal/feed/"),
    ("Gran Cursos Online",             "https://www.grancursosonline.com.br/blog/feed/"),
]

CARREIRAS = ["delegado", "delegada", "polícia civil", "pc ", "pcsp", "pcrj", "pcpr", "pcrs", "pcba", "pcmg", "investigador", "escrivão"]

EVENTOS = [
    "edital", "banca", "gabarito", "resultado", "regulamento",
    "concurso", "inscrição", "prova", "aprovado", "nomeação",
    "previsão", "previsto", "vagas", "seleção", "certame",
]

def relevante(text):
    t = text.lower()
    return any(c in t for c in CARREIRAS) and any(e in t for e in EVENTOS)

def parse_feed(source_name, url):
    try:
        r = requests.get(url, headers={"User-Agent": "Mozilla/5.0"}, timeout=10)
        r.raise_for_status()
        root = ET.fromstring(r.content)
    except Exception:
        return []
    
    items = []
    for item in root.findall(".//item"):
        title   = (item.find("title").text   or "").strip()
        excerpt = (item.find("description").text or "").strip()
        date    = (item.find("pubDate").text  or "").strip()
        
        # Limpa HTML do excerpt se houver
        import re
        excerpt = re.sub(r"<[^>]+>", "", excerpt)[:200].strip()
        
        if not title or not relevante(title + " " + excerpt):
            continue
        
        items.append({
            "title":   title,
            "excerpt": excerpt,
            "date":    date[:16] if date else "",
            "source":  source_name,
        })
    return items

def fetch_news(limit=20):
    now = time.time()
    cached = _cache.get(CATEGORY)
    if cached and (now - cached[0]) < CACHE_TTL:
        return cached[1][:limit]
    
    all_items = []
    seen = set()
    for name, url in FEEDS:
        for item in parse_feed(name, url):
            if item["title"] not in seen:
                seen.add(item["title"])
                all_items.append(item)
    
    # Ordena por data (mais recente primeiro)
    all_items.sort(key=lambda x: x["date"], reverse=True)
    _cache[CATEGORY] = (now, all_items)
    return all_items[:limit]

class handler(BaseHTTPRequestHandler):
    def do_GET(self):
        news = fetch_news()
        data = json.dumps({
            "category": CATEGORY,
            "label":    LABEL,
            "count":    len(news),
            "items":    news,
        }, ensure_ascii=False).encode("utf-8")
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
