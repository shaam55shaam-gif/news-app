from flask import Flask, request, Response
import feedparser, urllib.parse, json, re
from datetime import datetime

app = Flask(__name__)

FEEDS = {
    "الكل": "https://news.google.com/rss?hl=ar&gl=EG&ceid=EG:ar",
    "عاجل 🔴": "https://news.google.com/rss/search?q=عاجل&hl=ar&gl=EG&ceid=EG:ar",
    "رياضة ⚽": "https://news.google.com/rss/search?q=رياضة&hl=ar&gl=EG&ceid=EG:ar",
    "اقتصاد 💰": "https://news.google.com/rss/search?q=اقتصاد&hl=ar&gl=EG&ceid=EG:ar",
    "سياسة 🏛️": "https://news.google.com/rss/search?q=سياسة&hl=ar&gl=EG&ceid=EG:ar"
}

def get_image(entry):
    if hasattr(entry, 'media_content'): return entry.media_content[0]['url']
    if hasattr(entry, 'media_thumbnail'): return entry.media_thumbnail[0]['url']
    m = re.search(r'<img[^>]+src="([^"]+)"', getattr(entry, 'description', ''))
    if m: return m.group(1)
    return "https://images.unsplash.com/photo-1504711434969-e33886168f5c?w=600"

def get_news(cat):
    try:
        feed = feedparser.parse(FEEDS.get(cat, FEEDS["الكل"]))
        return [{"title":e.title,"link":e.link,"time":getattr(e,'published','')[:22],"source":getattr(e.source,'title','Google') if hasattr(e,'source') else "Google","image":get_image(e),"wa":f"https://wa.me/?text={urllib.parse.quote(e.title+' '+e.link)}"} for e in feed.entries[:20]]
    except: return []

# --- هاد اللي بيصلح مشكلة Missing Name ---
@app.route('/manifest.json')
def manifest():
    data = {
        "name": "أخبار شامي - Shami News",
        "short_name": "شامي نيوز",
        "description": "أخبار شامي مباشرة 24 ساعة",
        "start_url": "/",
        "scope": "/",
        "display": "standalone",
        "orientation": "any",
        "background_color": "#b71c1c",
        "theme_color": "#b71c1c",
        "lang": "ar",
        "dir": "rtl",
        "icons": [
            {"src": "https://cdn-icons-png.flaticon.com/512/21/21601.png","sizes": "192x192","type": "image/png","purpose": "any maskable"},
            {"src": "https://cdn-icons-png.flaticon.com/512/21/21601.png","sizes": "512x512","type": "image/png","purpose": "any maskable"}
        ]
    }
    # مهم جداً: ensure_ascii=False مشان العربي
    return Response(json.dumps(data, ensure_ascii=False), mimetype='application/manifest+json', headers={"Access-Control-Allow-Origin":"*"})

@app.route('/sw.js')
def sw():
    js = "const C='shami-v2';self.addEventListener('install',e=>{self.skipWaiting()});self.addEventListener('activate',e=>{self.clients.claim()});self.addEventListener('fetch',e=>{e.respondWith(fetch(e.request).catch(()=>caches.match(e.request)))})"
    return Response(js, mimetype='application/javascript')

@app.route('/')
def home():
    cat = request.args.get('cat','الكل')
    news = get_news(cat)
    tabs = "".join([f'<a href="/?cat={urllib.parse.quote(k)}" class="tab {"active" if k==cat else ""}">{k}</a>' for k in FEEDS])
    cards=""
    for i,n in enumerate(news):
        ad = '<div class="card ad">مساحة إعلانية AdSense</div>' if i==5 else ""
        cards+=f'<div class="card"><img src="{n["image"]}" loading="lazy"><div class="body"><span>{n["source"]} | {n["time"]}</span><h2><a href="{n["link"]}" target="_blank">{n["title"]}</a></h2><div class="btns"><a href="{n["link"]}" target="_blank" class="r">اقرأ ↗</a><a href="{n["wa"]}" target="_blank" class="w">واتساب</a></div></div></div>{ad}'
    return f"""<!doctype html><html dir="rtl" lang="ar"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
    <title>أخبار شامي</title><link rel="manifest" href="/manifest.json"><meta name="theme-color" content="#b71c1c">
    <style>*{{box-sizing:border-box}}body{{margin:0;font-family:Tahoma;background:#f0f2f5}}.h{{background:#b71c1c;color:#fff;padding:16px;text-align:center;position:sticky;top:0;z-index:10}}.tabs{{display:flex;gap:8px;overflow:auto;padding:10px;background:#fff;position:sticky;top:68px}}.tab{{padding:8px 14px;background:#eee;border-radius:20px;text-decoration:none;color:#333;white-space:nowrap}}.tab.active{{background:#d32f2f;color:#fff}}.c{{max-width:700px;margin:auto;padding:10px}}.card{{background:#fff;border-radius:12px;overflow:hidden;margin:12px 0;box-shadow:0 2px 8px rgba(0,0,0,.08)}}.card img{{width:100%;height:200px;object-fit:cover}}.body{{padding:12px}}.body h2{{font-size:17px;margin:8px 0}}a{{text-decoration:none}}.btns{{display:flex;gap:8px}}.r,.w{{flex:1;text-align:center;padding:10px;border-radius:8px;color:#fff;font-weight:bold}}.r{{background:#111}}.w{{background:#25D366}}.ad{{background:#fff9c4;border:2px dashed #fbc02d;padding:12px;text-align:center}}</style></head>
    <body><div class="h"><h1>🔥 أخبار شامي</h1></div><div class="tabs">{tabs}</div><div class="c">{cards}</div><script>if('serviceWorker' in navigator){{navigator.serviceWorker.register('/sw.js')}}</script></body></html>"""

if __name__=='__main__': app.run(host='0.0.0.0', port=10000)
