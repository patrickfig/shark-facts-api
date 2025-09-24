from flask import Flask, request, jsonify
import requests, datetime, urllib.parse, re

app = Flask(__name__)

WIKI_SEARCH = "https://{lang}.wikipedia.org/w/api.php"
WIKI_SUMMARY = "https://{lang}.wikipedia.org/api/rest_v1/page/summary/{title}"

def clean(text, max_len):
    t = re.sub(r"\s+", " ", text or "").strip()
    t = re.sub(r"\[[^\]]*?\]", "", t)
    return t if len(t) <= max_len else (t[:max_len-1] + "…")

def fetch_fact(lang, max_len):
    query = "tubarão OR tubarões" if lang == "pt" else "shark OR sharks"
    r = requests.get(WIKI_SEARCH.format(lang=lang), params={
        "action":"query","list":"search","format":"json","srlimit":50,"srsearch":query
    }, headers={"User-Agent":"shark-facts/1.0"})
    r.raise_for_status()
    items = r.json().get("query", {}).get("search", [])
    if not items: raise RuntimeError("Nada encontrado")
    today = datetime.date.today().isoformat()
    pick = items[abs(hash(today)) % len(items)]
    title = pick["title"]
    title_enc = urllib.parse.quote(title)
    s = requests.get(WIKI_SUMMARY.format(lang=lang, title=title_enc),
                     headers={"User-Agent":"shark-facts/1.0"})
    s.raise_for_status()
    data = s.json()
    url = data.get("content_urls", {}).get("desktop", {}).get("page") or \
          f"https://{lang}.wikipedia.org/wiki/{title_enc}"
    fact = clean(data.get("extract") or "", max_len)
    if not fact: raise RuntimeError("Resumo vazio")
    return {"fact": fact, "title": title, "lang": lang, "source": "Wikipedia", "url": url, "date": today}

@app.route("/")
def shark_fact():
    lang = request.args.get("lang","pt")
    if lang not in ("pt","en"): lang = "pt"
    try:
        max_len = max(min(int(request.args.get("max_length", "220")), 400), 60)
    except ValueError:
        max_len = 220
    try:
        payload = fetch_fact(lang, max_len)
        resp = jsonify(payload)
        resp.headers["Cache-Control"] = "no-store"
        resp.headers["Access-Control-Allow-Origin"] = "*"
        return resp
    except Exception as e:
        resp = jsonify({"error":"failed_to_fetch","message":str(e)})
        resp.status_code = 502
        resp.headers["Cache-Control"] = "no-store"
        resp.headers["Access-Control-Allow-Origin"] = "*"
        return resp
