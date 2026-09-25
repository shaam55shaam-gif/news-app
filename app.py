from flask import Flask, request, Response, jsonify
import feedparser, urllib.parse, re
from datetime import datetime

app = Flask(__name__)

FEEDS = {
    "الكل": "https://news.google.com/rss?hl=ar&gl=EG&ceid=EG:ar",
    "عاجل 🔴": "https://news.google.com/rss/search?q=عاجل&hl=ar&gl=EG&ceid=EG:ar",
    "رياضة ⚽": "https://news.google.com/rss/search?q=رياضة&hl=ar&gl=EG&ceid=EG:ar",
    "اقتصاد 💰": "https://news.google.com/rss/search?q=اقتصاد&hl=ar&gl=EG&ceid=EG:ar",
    "سياسة 🏛️": "https://news.google.com/rss/search?q=سياسة&hl=ar&gl=EG&ceid=EG:ar"
}

def extract_real_image(entry):
    if hasattr(entry, 'media_content'):
        for m in entry.media_content:
            if 'url' in m: return m['url']
    if hasattr(entry, 'media_thumbnail'): return entry.media_thumbnail[0]['url']
    if hasattr(entry, 'enclosures') and entry.enclosures: return entry.enclosures[0].get('href','')
    if hasattr(entry, 'description'):
        import re
        match = re.search(r'<img[^>]+src="([^"]+)"', entry.description)
        if match: return match.group(1)
    return "https://images.unsplash.com/photo-1504711434969-e33886168f5c?w=600"

def get_news(cat):
    try:
        feed = feedparser.parse(FEEDS.get(cat, FEEDS["الكل"]))
        return [{"title":e.title,"link":e.link,"time":e.published[:22] if hasattr(e,'published') else "","source":e.source.title if hasattr(e,'source') else "Google","image":extract_real_image(e),"wa":f"https://wa.me/?text={urllib.parse.quote(e.title+' - '+e.link)}"} for e in feed.entries[:20]]
    except: return []

# --- هون كان الخطأ وصلحناه ---
@app.route('/manifest.json')
@app.route('/manifest.webmanifest')
def manifest():
    data = {
        "name": "أخبار شامي - Shami News",
        "short_name": "شامي نيوز",
        "description": "أخبار شامي مباشرة 24 ساعة - تطبيق أخبار سوري عاجل رياضة اقتصاد",
        "start_url": "/",
        "scope": "/",
        "display": "standalone",
        "background_color": "#b71c1c",
        "theme_color": "#b71c1c",
        "lang": "ar",
        "dir": "rtl",
        "icons": [
            {"src": "https://cdn-icons-png.flaticon.com/512/21/21601.png", "sizes": "192x192", "type": "image/png", "purpose": "any maskable"},
            {"src": "https://cdn-icons-png.flaticon.com/512/21/21601.png", "sizes": "512x512", "type": "image/png", "purpose": "any maskable"}
        ]
    }
    return jsonify(data)

@app.route('/sw.js')
def sw():
    js = """
    const CACHE='shami-v1';
    self.addEventListener('install', e=>{self.skipWaiting();});
    self.addEventListener('activate', e=>{self.clients.claim();});
    self.addEventListener('fetch', e=>{e.respondWith(fetch(e.request).catch(()=>caches.match(e.request)));});
    """
    return Response(js, mimetype='application/javascript')

@app.route('/')
def home():
    cat = request.args.get('cat','الكل')
    news_list = get_news(cat)
    tabs = "".join([f'<a href="/?cat={urllib.parse.quote(n)}" class="tab {"active" if n==cat else ""}">{n}</a>' for n in FEEDS.keys()])
    cards=""
    for idx,n in enumerate(news_list):
        ad = '<div class="card ad"><small>مساحة إعلانية AdSense</small></div>' if idx==4 else ""
        cards+=f'<div class="card"><img src="{n["image"]}" loading="lazy"><div class="card-body"><span class="source">{n["source"]} | {n["time"]}</span><h2><a href="{n["link"]}" target="_blank">{n["title"]}</a></h2><div class="actions"><a href="{n["link"]}" target="_blank" class="btn read">اقرأ ↗</a><a href="{n["wa"]}" target="_blank" class="btn wa">واتساب 💬</a></div></div></div>{ad}'
    return f"""
    <html dir="rtl" lang="ar"><head>
    <meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
    <title>أخبار شامي</title>
    <link rel="manifest" href="/manifest.json">
    <link rel="manifest" href="/manifest.webmanifest">
    <meta name="theme-color" content="#b71c1c">
    <script async src="https://pagead2.googlesyndication.com/pagead/js/adsbygoogle.js?client=ca-pub-XXXX" crossorigin="anonymous"></script>
    <style>
    *{{box-sizing:border-box}} body{{font-family:Tahoma;background:#f0f2f5;margin:0}}
   .header{{background:#b71c1c;color:white;padding:18px;text-align:center;position:sticky;top:0;z-index:10}}
   .tabs{{display:flex;gap:8px;overflow-x:auto;padding:12px;background:white;position:sticky;top:76px;z-index:9}}
   .tab{{white-space:nowrap;padding:8px 16px;border-radius:20px;background:#eee;text-decoration:none;color:#333;font-weight:bold}}.tab.active{{background:#d32f2f;color:white}}
   .container{{max-width:750px;margin:auto;padding:10px}}.card{{background:white;border-radius:14px;overflow:hidden;margin:14px 0;box-shadow:0 3px 10px rgba(0,0,0,0.08)}}
   .card img{{width:100%;height:220px;object-fit:cover}}.card-body{{padding:14px}}.source{{color:#888;font-size:12px}}
   .card h2{{margin:8px 0 12px;font-size:18px}}.card h2 a{{text-decoration:none;color:#111}}
   .actions{{display:flex;gap:10px}}.btn{{flex:1;text-align:center;padding:10px;border-radius:8px;text-decoration:none;font-weight:bold}}
   .btn.read{{background:#111;color:white}}.btn.wa{{background:#25D366;color:white}}.card.ad{{background:#fff9c4;border:2px dashed #fbc02d;padding:15px;text-align:center}}
    </style></head>
    <body><div class="header"><h1>🔥 أخبار شامي</h1></div><div class="tabs">{tabs}</div><div class="container">{cards}</div>
    <script>if('serviceWorker' in navigator){{navigator.serviceWorker.register('/sw.js');}}</script>
    </body></html>"""

if __name__ == '__main__': app.run(host='0.0.0.0', port=10000)
