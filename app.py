from flask import Flask, request, Response
import feedparser
from datetime import datetime
import urllib.parse
import re

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
    if hasattr(entry, 'media_thumbnail'):
        return entry.media_thumbnail[0]['url']
    if hasattr(entry, 'enclosures') and len(entry.enclosures)>0:
        if 'href' in entry.enclosures[0]: return entry.enclosures[0]['href']
    if hasattr(entry, 'description'):
        match = re.search(r'<img[^>]+src="([^"]+)"', entry.description)
        if match: return match.group(1)
    return "https://images.unsplash.com/photo-1504711434969-e33886168f5c?w=600"

def get_news(category="الكل"):
    url = FEEDS.get(category, FEEDS["الكل"])
    try:
        feed = feedparser.parse(url)
        news = []
        for entry in feed.entries[:20]:
            news.append({
                "title": entry.title,
                "link": entry.link,
                "time": entry.published[:22] if hasattr(entry, 'published') else "",
                "source": entry.source.title if hasattr(entry, 'source') else "Google News",
                "image": extract_real_image(entry),
                "wa": f"https://wa.me/?text={urllib.parse.quote(entry.title + ' - ' + entry.link)}"
            })
        return news
    except: return []

# ملفات التطبيق
@app.route('/manifest.json')
def manifest():
    return {
        "name": "أخبار شامي",
        "short_name": "شامي نيوز",
        "description": "أخبار مباشرة 24 ساعة",
        "start_url": "/",
        "display": "standalone",
        "background_color": "#b71c1c",
        "theme_color": "#b71c1c",
        "icons": [
            {"src": "https://cdn-icons-png.flaticon.com/512/21/21601.png", "sizes": "512x512", "type": "image/png"}
        ]
    }

@app.route('/sw.js')
def sw():
    js = "self.addEventListener('fetch', e=>{e.respondWith(fetch(e.request).catch(()=>caches.match(e.request)))})"
    return Response(js, mimetype='application/javascript')

@app.route('/')
def home():
    cat = request.args.get('cat', 'الكل')
    news_list = get_news(cat)
    tabs = "".join([f'<a href="/?cat={urllib.parse.quote(n)}" class="tab {"active" if n==cat else ""}">{n}</a>' for n in FEEDS.keys()])
    cards = ""
    for idx, n in enumerate(news_list):
        ad = '<div class="card ad"><small>مساحة إعلانية</small><p>هنا كود AdSense الحقيقي</p></div>' if idx==4 else ""
        cards += f"""
        <div class="card">
            <img src="{n['image']}" loading="lazy" onerror="this.src='https://images.unsplash.com/photo-1504711434969-e33886168f5c?w=600'">
            <div class="card-body">
                <span class="source">{n['source']} | {n['time']}</span>
                <h2><a href="{n['link']}" target="_blank">{n['title']}</a></h2>
                <div class="actions">
                    <a href="{n['link']}" target="_blank" class="btn read">اقرأ من المصدر ↗</a>
                    <a href="{n['wa']}" target="_blank" class="btn wa">واتساب 💬</a>
                </div>
            </div>
        </div>{ad}"""

    return f"""
    <html dir="rtl" lang="ar"><head>
        <meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
        <title>أخبار شامي</title>
        <link rel="manifest" href="/manifest.json">
        <meta name="theme-color" content="#b71c1c">
        <link rel="apple-touch-icon" href="https://cdn-icons-png.flaticon.com/512/21/21601.png">
        <style>
            *{{box-sizing:border-box}} body{{font-family:Tahoma,Arial;background:#f0f2f5;margin:0}}
           .header{{background:#b71c1c;color:white;padding:18px;text-align:center;position:sticky;top:0;z-index:10}}
           .install{{background:#ffeb3b;color:#111;padding:10px;text-align:center;font-weight:bold;display:none}}
           .tabs{{display:flex;gap:8px;overflow-x:auto;padding:12px;background:white;position:sticky;top:76px;z-index:9;box-shadow:0 2px 5px rgba(0,0,0,0.1)}}
           .tab{{white-space:nowrap;padding:8px 16px;border-radius:20px;background:#eee;text-decoration:none;color:#333;font-weight:bold}}
           .tab.active{{background:#d32f2f;color:white}}
           .container{{max-width:750px;margin:auto;padding:10px}}
           .card{{background:white;border-radius:14px;overflow:hidden;margin:14px 0;box-shadow:0 3px 10px rgba(0,0,0,0.08)}}
           .card img{{width:100%;height:220px;object-fit:cover}}
           .card-body{{padding:14px}}.source{{color:#888;font-size:12px}}
           .card h2{{margin:8px 0 12px;font-size:18px;line-height:1.6}}.card h2 a{{text-decoration:none;color:#111}}
           .actions{{display:flex;gap:10px}}.btn{{flex:1;text-align:center;padding:10px;border-radius:8px;text-decoration:none;font-weight:bold;font-size:14px}}
           .btn.read{{background:#111;color:white}}.btn.wa{{background:#25D366;color:white}}
           .card.ad{{background:#fff9c4;border:2px dashed #fbc02d;padding:15px;text-align:center}}
        </style></head>
    <body>
        <div class="header"><h1>🔥 أخبار شامي</h1><p>ثبت التطبيق من المتصفح - {cat} - {datetime.now().strftime('%H:%M')}</p></div>
        <div id="installBanner" class="install">📲 اضغط هنا لتثبيت التطبيق على جوالك <button id="installBtn" style="margin-right:10px;padding:6px 12px;background:#111;color:white;border:none;border-radius:6px">تثبيت</button></div>
        <div class="tabs">{tabs}</div>
        <div class="container">{cards}</div>
        <script>
            if('serviceWorker' in navigator){{navigator.serviceWorker.register('/sw.js')}}
            let deferredPrompt; const banner=document.getElementById('installBanner');
            window.addEventListener('beforeinstallprompt', (e)=>{{e.preventDefault(); deferredPrompt=e; banner.style.display='block';}});
            document.getElementById('installBtn').addEventListener('click', async()=>{{ if(deferredPrompt){{deferredPrompt.prompt(); await deferredPrompt.userChoice; deferredPrompt=null; banner.style.display='none';}} }});
        </script>
    </body></html>
    """

if __name__ == '__main__':
    app.run()
