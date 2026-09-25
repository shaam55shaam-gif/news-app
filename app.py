from flask import Flask, request, Response, redirect, session
import feedparser, urllib.parse, json, re, os
from datetime import datetime

app = Flask(__name__)
app.secret_key = "shami_secret_2026_very_secure"

FEEDS = {
    "الكل": "https://news.google.com/rss?hl=ar&gl=EG&ceid=EG:ar",
    "عاجل 🔴": "https://news.google.com/rss/search?q=عاجل&hl=ar&gl=EG&ceid=EG:ar",
    "رياضة ⚽": "https://news.google.com/rss/search?q=رياضة&hl=ar&gl=EG&ceid=EG:ar",
    "اقتصاد 💰": "https://news.google.com/rss/search?q=اقتصاد&hl=ar&gl=EG&ceid=EG:ar",
    "سياسة 🏛️": "https://news.google.com/rss/search?q=سياسة&hl=ar&gl=EG&ceid=EG:ar"
}

# === الميزة الجديدة 1: أخبارك الخاصة ===
CUSTOM_FILE = "custom_news.json"
CUSTOM_NEWS = []

def load_custom():
    global CUSTOM_NEWS
    if os.path.exists(CUSTOM_FILE):
        try:
            with open(CUSTOM_FILE, "r", encoding="utf-8") as jf:
                CUSTOM_NEWS = json.load(jf)
        except:
            CUSTOM_NEWS = []
load_custom()

def save_custom():
    try:
        with open(CUSTOM_FILE, "w", encoding="utf-8") as jf:
            json.dump(CUSTOM_NEWS, jf, ensure_ascii=False, indent=2)
    except: pass

def get_image(entry):
    if hasattr(entry, 'media_content'): return entry.media_content[0]['url']
    if hasattr(entry, 'media_thumbnail'): return entry.media_thumbnail[0]['url']
    m = re.search(r'<img[^>]+src="([^"]+)"', getattr(entry, 'description', ''))
    if m: return m.group(1)
    return "https://images.unsplash.com/photo-1504711434969-e33886168f5c?w=600"

def get_news(cat):
    custom_filtered = [n for n in CUSTOM_NEWS if cat == "الكل" or n.get("category")==cat]
    try:
        feed = feedparser.parse(FEEDS.get(cat, FEEDS["الكل"]))
        google_news = [{"title":e.title,"link":e.link,"time":getattr(e,'published','')[:22],"source":getattr(e.source,'title','Google') if hasattr(e,'source') else "Google","image":get_image(e),"wa":f"https://wa.me/?text={urllib.parse.quote(e.title+' '+e.link)}","is_custom":False} for e in feed.entries[:20]]
        return custom_filtered + google_news
    except:
        return custom_filtered

@app.route('/manifest.json')
def manifest():
    data = {"name": "أخبار شامي - Shami News","short_name": "شامي نيوز","description": "أخبار شامي مباشرة 24 ساعة","start_url": "/","scope": "/","display": "standalone","background_color": "#b71c1c","theme_color": "#b71c1c","lang": "ar","dir": "rtl","icons": [{"src": "https://cdn-icons-png.flaticon.com/512/21/21601.png","sizes": "192x192","type": "image/png"},{"src": "https://cdn-icons-png.flaticon.com/512/21/21601.png","sizes": "512x512","type": "image/png"}]}
    return Response(json.dumps(data, ensure_ascii=False), mimetype='application/manifest+json')

@app.route('/sw.js')
def sw():
    js = "const C='shami-v2';self.addEventListener('install',e=>{self.skipWaiting()});self.addEventListener('activate',e=>{self.clients.claim()});self.addEventListener('fetch',e=>{e.respondWith(fetch(e.request).catch(()=>caches.match(e.request)))})"
    return Response(js, mimetype='application/javascript')

ADMIN_PASSWORD = "shami123"

@app.route('/admin', methods=['GET','POST'])
def admin():
    if request.args.get('logout'):
        session.pop('admin', None)
        return redirect('/admin')
    if request.method == 'POST':
        if request.form.get('password'):
            if request.form.get('password') == ADMIN_PASSWORD:
                session['admin'] = True
            else:
                return "<h2 style='text-align:center;color:red'>الباسوورد غلط ❌</h2><a href='/admin'>رجوع</a>"
        elif session.get('admin') and request.form.get('title'):
            title = request.form.get('title').strip()
            if title:
                CUSTOM_NEWS.insert(0, {"title": title,"link": request.form.get('link') or "#","time": datetime.now().strftime("%H:%M"),"source": "خاص - شامي 🔥","image": request.form.get('image') or "https://images.unsplash.com/photo-1504711434969-e33886168f5c?w=600","wa": f"https://wa.me/?text={urllib.parse.quote(title)}","is_custom": True,"category": request.form.get('category','الكل'),"urgent": request.form.get('urgent')=="on"})
                save_custom()
        elif session.get('admin') and request.form.get('delete_index') is not None:
            try:
                CUSTOM_NEWS.pop(int(request.form.get('delete_index')))
                save_custom()
            except: pass
    if not session.get('admin'):
        return """<!doctype html><html dir=rtl lang=ar><head><meta charset=utf-8><meta name=viewport content=width=device-width,initial-scale=1><title>دخول</title>
        <style>body{font-family:Tahoma;background:#f0f2f5;display:flex;align-items:center;justify-content:center;height:100vh;margin:0}.box{background:#fff;padding:30px;border-radius:12px;width:320px;text-align:center}input{width:100%;padding:12px;margin:10px 0}button{width:100%;padding:12px;background:#b71c1c;color:#fff;border:0;border-radius:8px}</style></head>
        <body><form class=box method=post><h2>🔐 لوحة شامي</h2><input type=password name=password placeholder=الباسوورد required><button>دخول</button><p style=font-size:12px;color:#888>shami123</p></form></body></html>"""
    lst=""
    for i,n in enumerate(CUSTOM_NEWS):
        lst+=f'<div style="background:#fff;padding:10px;border-radius:8px;margin:8px 0;display:flex;justify-content:space-between"><span>{n["title"][:40]}</span><form method=post><input type=hidden name=delete_index value={i}><button style="background:red;color:#fff;border:0;padding:5px 10px;border-radius:6px">حذف</button></form></div>'
    return f"""<!doctype html><html dir=rtl lang=ar><head><meta charset=utf-8><meta name=viewport content=width=device-width,initial-scale=1><title>لوحة التحكم</title>
    <style>body{{font-family:Tahoma;background:#f0f2f5;margin:0}}.h{{background:#b71c1c;color:#fff;padding:16px;text-align:center}}.c{{max-width:600px;margin:auto;padding:15px}}input,select{{width:100%;padding:12px;margin:6px 0;border:1px solid #ddd;border-radius:8px}}.btn{{width:100%;background:#b71c1c;color:#fff;padding:12px;border:0;border-radius:8px;font-size:18px}}</style></head>
    <body><div class=h><h2>⚙️ لوحة تحكم شامي</h2><a href=/ style=color:#fff>رجوع للموقع</a> | <a href=/admin?logout=1 style=color:#ffcccb>خروج</a></div>
    <div class=c><form method=post style=background:#fff;padding:15px;border-radius:12px><input name=title placeholder="عنوان الخبر *" required><input name=image placeholder="رابط الصورة"><input name=link placeholder="رابط الخبر"><select name=category><option>الكل</option><option>عاجل 🔴</option><option>رياضة ⚽</option><option>اقتصاد 💰</option><option>سياسة 🏛️</option></select><label><input type=checkbox name=urgent style=width:auto> عاجل</label><button class=btn>نشر 🚀</button></form><h3>أخبارك ({len(CUSTOM_NEWS)}):</h3>{lst}</div></body></html>"""

@app.route('/')
def home():
    cat = request.args.get('cat','الكل')
    news = get_news(cat)
    tabs = "".join([f'<a href="/?cat={urllib.parse.quote(k)}" class="tab {"active" if k==cat else ""}">{k}</a>' for k in FEEDS])
    cards=""
    for i,n in enumerate(news):
        ad = '<div class="card" style="background:#fff9c4;border:2px dashed #fbc02d;padding:12px;text-align:center">مساحة إعلانية AdSense</div>' if i==5 else ""
        badge = '<div style="background:#b71c1c;color:#fff;padding:4px 8px;font-size:12px;position:absolute;top:0;right:0">خاص - شامي 🔥</div>' if n.get('is_custom') else ''
        style = 'border:2px solid #d32f2f' if n.get('urgent') else ''
        cards+=f'<div class="card" style="position:relative;{style}">{badge}<img src="{n["image"]}" loading="lazy"><div class="body"><span>{n["source"]} | {n["time"]}</span><h2><a href="{n["link"]}" target="_blank">{n["title"]}</a></h2><div class="btns"><a href="{n["link"]}" target="_blank" class="r">اقرأ ↗</a><a href="{n["wa"]}" target="_blank" class="w">واتساب</a></div></div></div>{ad}'
    return f"""<!doctype html><html dir="rtl" lang="ar"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>أخبار شامي</title><link rel="manifest" href="/manifest.json"><meta name="theme-color" content="#b71c1c">
    <style>*{{box-sizing:border-box}}body{{margin:0;font-family:Tahoma;background:#f0f2f5}}.h{{background:#b71c1c;color:#fff;padding:16px;text-align:center;position:sticky;top:0;z-index:10}}.tabs{{display:flex;gap:8px;overflow:auto;padding:10px;background:#fff;position:sticky;top:68px}}.tab{{padding:8px 14px;background:#eee;border-radius:20px;text-decoration:none;color:#333;white-space:nowrap}}.tab.active{{background:#d32f2f;color:#fff}}.c{{max-width:700px;margin:auto;padding:10px}}.card{{background:#fff;border-radius:12px;overflow:hidden;margin:12px 0;box-shadow:0 2px 8px rgba(0,0,0,.08)}}.card img{{width:100%;height:200px;object-fit:cover}}.body{{padding:12px}}.body h2{{font-size:17px;margin:8px 0}}a{{text-decoration:none}}.btns{{display:flex;gap:8px}}.r,.w{{flex:1;text-align:center;padding:10px;border-radius:8px;color:#fff;font-weight:bold}}.r{{background:#111}}.w{{background:#25D366}}</style></head>
    <body><div class="h"><h1>🔥 أخبار شامي</h1></div><div class="tabs">{tabs}</div><div class="c">{cards}</div><script>if('serviceWorker' in navigator){{navigator.serviceWorker.register('/sw.js')}}</script></body></html>"""

if __name__=='__main__': app.run(host='0.0.0.0', port=10000)
