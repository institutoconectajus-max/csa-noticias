import time, json, re, os, requests
import xml.etree.ElementTree as ET
from http.server import BaseHTTPRequestHandler

CATEGORY  = "promotoria"
LABEL     = "Ministério Público"
CACHE_TTL = 3600
_cache    = {}

FEEDS = [
    ("Estratégia Carreiras Jurídicas", "https://cj.estrategia.com/portal/feed/"),
    ("Gran Cursos Online",             "https://www.grancursosonline.com.br/blog/feed/"),
]

CARREIRAS = ["ministério público", "promotor", "promotora", "promotoria", "procurador de justiça", "mpsp", "mprj", "mppr", "mpf"]
EVENTOS   = ["edital", "banca", "gabarito", "resultado", "regulamento", "concurso",
             "inscrição", "prova", "aprovado", "nomeação", "previsão", "vagas", "certame"]

HEADERS = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}

def clean(text):
    return re.sub(r"<[^>]+>", "", text or "").strip()

def relevante(text):
    t = text.lower()
    return any(c in t for c in CARREIRAS) and any(e in t for e in EVENTOS)

def resumir(title, excerpt):
    key = os.environ.get("GEMINI_API_KEY", "")
    if not key:
        return excerpt[:200] if excerpt else ""
    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-3.5-flash-lite:generateContent?key={key}"
    try:
        prompt = (
            f"Resuma em 2 frases objetivas em português esta notícia de concurso público jurídico. "
            f"Seja direto, sem introdução. Título: {title}. Texto: {excerpt[:600]}"
        )
        r = requests.post(url, json={
            "contents": [{"parts": [{"text": prompt}]}],
            "generationConfig": {"maxOutputTokens": 120, "temperature": 0.2}
        }, timeout=8)
        resp = r.json()
        if "candidates" in resp:
            return resp["candidates"][0]["content"]["parts"][0]["text"].strip()
        return excerpt[:200] if excerpt else ""
    except Exception:
        return excerpt[:200] if excerpt else ""

def fetch_news(limit=20):
    now = time.time()
    cached = _cache.get(CATEGORY)
    if cached and (now - cached[0]) < CACHE_TTL:
        return cached[1][:limit]

    all_items = []
    seen = set()
    for source_name, url in FEEDS:
        try:
            r = requests.get(url, headers=HEADERS, timeout=10)
            root = ET.fromstring(r.content)
        except Exception:
            continue
        for item in root.findall(".//item"):
            title   = clean(item.find("title").text if item.find("title") is not None else "")
            excerpt = clean(item.find("description").text if item.find("description") is not None else "")
            date    = (item.find("pubDate").text or "")[:16].strip()
            if not title or title in seen: continue
            if not relevante(title + " " + excerpt): continue
            seen.add(title)
            resumo = resumir(title, excerpt)
            all_items.append({"title": title, "resumo": resumo, "date": date, "source": source_name})

    all_items.sort(key=lambda x: x["date"], reverse=True)
    _cache[CATEGORY] = (now, all_items)
    return all_items[:limit]

class handler(BaseHTTPRequestHandler):
    def do_GET(self):
        news = fetch_news()
        data = json.dumps({"category": CATEGORY, "label": LABEL, "count": len(news), "items": news},
                          ensure_ascii=False).encode("utf-8")
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
