from flask import Flask, request, Response, redirect, session, jsonify
import feedparser, urllib.parse, json, re, os
from datetime import datetime

app = Flask(__name__)
app.secret_key = "shami_secret_2026_very_secure"

FEEDS = {
    "الكل": "https://news.google.com/rss?hl=ar&gl=EG&ceid=EG:ar",
    "عاجل 🔴": "https://news.google.com/rss/search?q=عاجل&hl=ar&gl=EG&ceid=EG:ar",
    "رياضة ⚽": "https://news.google.com/rss/search?q=رياضة&hl=ar&gl=EG&ceid=EG:ar",
    "اقتصاد 💰": "https://news.google.com/rss/search?q=اقتصاد&hl=ar&gl=EG&ceid=EG:ar",
    "سياسة 🏛️": "https://news.google.com/rss/search?q=سياسة&hl=ar&gl=EG&ceid=EG:ar",
    "ثقافية 🎭": "https://news.google.com/rss/search?q=ثقافة&hl=ar&gl=EG&ceid=EG:ar"
}

CUSTOM_FILE = "custom_news.json"
CUSTOM_NEWS = []
def load_custom():
    global CUSTOM_NEWS
    if os.path.exists(CUSTOM_FILE):
        try: CUSTOM_NEWS = json.load(open(CUSTOM_FILE, encoding="utf-8"))
        except: pass
load_custom()
def save_custom():
    try: json.dump(CUSTOM_NEWS, open(CUSTOM_FILE,"w",encoding="utf-8"), ensure_ascii=False, indent=2)
    except: pass

def get_image(entry):
    if hasattr(entry, 'media_content'): return entry.media_content[0]['url']
    if hasattr(entry, 'media_thumbnail'): return entry.media_thumbnail[0]['url']
    m = re.search(r'<img[^>]+src="([^"]+)"', getattr(entry, 'description', ''))
    if m: return m.group(1)
    return "https://images.unsplash.com/photo-1504711434969-e33886168f5c?w=600"

def get_news(cat):
    cf = [n for n in CUSTOM_NEWS if cat == "الكل" or n.get("category")==cat or n.get("category")=="الكل"]
    try:
        feed = feedparser.parse(FEEDS.get(cat, FEEDS["الكل"]))
        gn = [{"title":e.title,"link":e.link,"time":getattr(e,'published','')[:22],"source":getattr(e.source,'title','Google') if hasattr(e,'source') else "Google","image":get_image(e),"wa":f"https://wa.me/?text={urllib.parse.quote(e.title+' '+e.link)}","is_custom":False, "category": cat} for e in feed.entries[:20]]
        return cf+gn
    except: return cf

# API جديد للتحديث كل دقيقة
@app.route('/api/news')
def api_news():
    cat = request.args.get('cat','الكل')
    return jsonify(get_news(cat))

@app.route('/manifest.json')
def manifest():
    data = {"name": "أخبار شامي - Shami News","short_name": "شامي نيوز","start_url": "/","display": "standalone","background_color": "#b71c1c","theme_color": "#b71c1c","lang": "ar","dir": "rtl","icons": [{"src": "https://cdn-icons-png.flaticon.com/512/21/21601.png","sizes": "192x192","type": "image/png"},{"src": "https://cdn-icons-png.flaticon.com/512/21/21601.png","sizes": "512x512","type": "image/png"}]}
    return Response(json.dumps(data, ensure_ascii=False), mimetype='application/manifest+json')

@app.route('/sw.js')
def sw():
    return Response("self.addEventListener('install',e=>{self.skipWaiting()});self.addEventListener('activate',e=>{self.clients.claim()});", mimetype='application/javascript')

ADMIN_PASSWORD = "shami123"
@app.route('/admin', methods=['GET','POST'])
def admin():
    if request.args.get('logout'):
        session.pop('admin', None)
        return redirect('/admin')
    if request.method == 'POST':
        if request.form.get('password'):
            if request.form.get('password') == ADMIN_PASSWORD: session['admin'] = True
            else: return "<h2 style='text-align:center;color:red'>غلط</h2><a href='/admin'>رجوع</a>"
        elif session.get('admin') and request.form.get('title'):
            CUSTOM_NEWS.insert(0, {"title": request.form.get('title'),"link": request.form.get('link') or "#","time": datetime.now().strftime("%H:%M"),"source": "خاص - شامي 🔥","image": request.form.get('image') or "https://images.unsplash.com/photo-1504711434969-e33886168f5c?w=600","wa": f"https://wa.me/?text={urllib.parse.quote(request.form.get('title'))}","is_custom": True,"category": request.form.get('category','الكل'),"urgent": request.form.get('urgent')=="on"})
            save_custom()
        elif session.get('admin') and request.form.get('delete_index') is not None:
            try: CUSTOM_NEWS.pop(int(request.form.get('delete_index'))); save_custom()
            except: pass
    if not session.get('admin'):
        return """<!doctype html><html dir=rtl><head><meta charset=utf-8><meta name=viewport content=width=device-width,initial-scale=1><style>body{font-family:Tahoma;background:#f0f2f5;display:flex;justify-content:center;align-items:center;height:100vh;margin:0}.box{background:#fff;padding:30px;border-radius:12px;width:320px;text-align:center}input{width:100%;padding:12px;margin:10px 0}button{width:100%;padding:12px;background:#b71c1c;color:#fff;border:0;border-radius:8px}</style></head><body><form class=box method=post><h2>🔐 شامي</h2><input type=password name=password placeholder=الباسوورد required><button>دخول</button></form></body></html>"""
    lst="".join([f'<div style="background:#fff;padding:10px;border-radius:8px;margin:8px 0;display:flex;justify-content:space-between"><span>{n["title"][:40]}</span><form method=post><input type=hidden name=delete_index value={i}><button style="background:red;color:#fff;border:0;padding:5px 10px;border-radius:6px">حذف</button></form></div>' for i,n in enumerate(CUSTOM_NEWS)])
    return f"""<!doctype html><html dir=rtl><head><meta charset=utf-8><meta name=viewport content=width=device-width,initial-scale=1><style>body{{font-family:Tahoma;background:#f0f2f5;margin:0}}.h{{background:#b71c1c;color:#fff;padding:16px;text-align:center}}.c{{max-width:600px;margin:auto;padding:15px}}input,select{{width:100%;padding:12px;margin:6px 0}}.btn{{width:100%;background:#b71c1c;color:#fff;padding:12px;border:0;border-radius:8px}}</style></head><body><div class=h><h2>لوحة تحكم</h2><a href=/ style=color:#fff>موقع</a> | <a href=/admin?logout=1 style=color:#ffcccb>خروج</a></div><div class=c><form method=post style=background:#fff;padding:15px;border-radius:12px><input name=title placeholder="عنوان *" required><input name=image placeholder="صورة"><input name=link placeholder="رابط"><select name=category><option>الكل</option><option>عاجل 🔴</option><option>رياضة ⚽</option><option>اقتصاد 💰</option><option>سياسة 🏛️</option><option>ثقافية 🎭</option></select><label><input type=checkbox name=urgent style=width:auto> عاجل</label><button class=btn>نشر</button></form><h3>أخبارك ({len(CUSTOM_NEWS)}):</h3>{lst}</div></body></html>"""

@app.route('/')
def home():
    cat = request.args.get('cat','الكل')
    news = get_news(cat)
    tabs = "".join([f'<a href="/?cat={urllib.parse.quote(k)}" class="tab {"active" if k==cat else ""}">{k}</a>' for k in FEEDS])
    cards=""
    for i,n in enumerate(news):
        ad = '<div class="card ad">مساحة إعلانية AdSense</div>' if i==5 else ""
        badge = '<div class="custom-badge">خاص - شامي 🔥</div>' if n.get('is_custom') else ''
        style = 'border:2px solid #d32f2f' if n.get('urgent') else ''
        cards+=f'<div class="card" style="{style}">{badge}<img src="{n["image"]}" loading="lazy"><div class="body"><span>{n["source"]} | {n["time"]}</span><h2><a href="{n["link"]}" target="_blank">{n["title"]}</a></h2><div class="btns"><a href="{n["link"]}" target="_blank" class="r">اقرأ ↗</a><a href="{n["wa"]}" target="_blank" class="w">واتساب</a></div></div></div>{ad}'
    return f"""<!doctype html><html dir="rtl" lang="ar"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>أخبار شامي</title><link rel="manifest" href="/manifest.json"><meta name="theme-color" content="#b71c1c">
    <style>*{{box-sizing:border-box}}:root{{--bg:#f0f2f5;--card:#fff;--text:#111;--tab:#eee}}body.dark{{--bg:#121212;--card:#1e1e1e;--text:#eee;--tab:#333}}body{{margin:0;font-family:Tahoma;background:var(--bg);color:var(--text);transition:.3s}}.h{{background:#b71c1c;color:#fff;padding:16px;text-align:center;position:sticky;top:0;z-index:10;display:flex;justify-content:space-between;align-items:center}}.h h1{{margin:0;font-size:20px}}.controls{{display:flex;gap:6px}}.ctrl{{background:rgba(255,255,255,.2);border:0;color:#fff;padding:6px 10px;border-radius:20px;cursor:pointer}}.tabs{{display:flex;gap:8px;overflow:auto;padding:10px;background:var(--card);position:sticky;top:68px;z-index:9}}.tab{{padding:8px 14px;background:var(--tab);border-radius:20px;text-decoration:none;color:var(--text);white-space:nowrap}}.tab.active{{background:#d32f2f;color:#fff}}.c{{max-width:700px;margin:auto;padding:10px}}.card{{background:var(--card);border-radius:12px;overflow:hidden;margin:12px 0;box-shadow:0 2px 8px rgba(0,0,0,.08);position:relative}}.card img{{width:100%;height:200px;object-fit:cover}}.body{{padding:12px}}.body h2{{font-size:var(--fs,17px);margin:8px 0}}a{{text-decoration:none;color:inherit}}.btns{{display:flex;gap:8px}}.r,.w{{flex:1;text-align:center;padding:10px;border-radius:8px;color:#fff;font-weight:bold}}.r{{background:#111}}.w{{background:#25D366}}.ad{{background:#fff9c4;border:2px dashed #fbc02d;padding:12px;text-align:center;color:#000}}.custom-badge{{background:#b71c1c;color:#fff;padding:4px 8px;font-size:12px;position:absolute;top:0;right:0}}.live{{display:inline-block;width:8px;height:8px;background:#0f0;border-radius:50%;animation:pulse 1s infinite;margin-left:5px}}@keyframes pulse{{0%{{opacity:1}}50%{{opacity:.3}}100%{{opacity:1}}}}#lastUpdate{{font-size:11px;opacity:.7;margin-top:5px}}</style></head>
    <body><div class="h"><div><h1>🔥 أخبار شامي <span class="live"></span></h1><div id="lastUpdate">آخر تحديث: الآن - يتحدث كل دقيقة</div></div><div class="controls"><button class="ctrl" onclick="changeFont(1)">A+</button><button class="ctrl" onclick="changeFont(-1)">A-</button><button class="ctrl" onclick="toggleDark()">🌙</button></div></div><div class="tabs">{tabs}</div><div class="c" id="newsContainer">{cards}</div>
    <script>
    const root=document.documentElement;let fs=parseInt(localStorage.getItem('fs')||17);
    function applyFS(){{root.style.setProperty('--fs',fs+'px');localStorage.setItem('fs',fs);}}
    function changeFont(d){{fs=Math.min(26,Math.max(13,fs+d));applyFS();}}applyFS();
    function toggleDark(){{document.body.classList.toggle('dark');localStorage.setItem('dark',document.body.classList.contains('dark'));}}
    if(localStorage.getItem('dark')=='true'){{document.body.classList.add('dark');}}
    if('serviceWorker' in navigator){{navigator.serviceWorker.register('/sw.js')}}
    // === التحديث التلقائي كل دقيقة ===
    const currentCat = new URLSearchParams(window.location.search).get('cat') || 'الكل';
    async function refreshNews(){{
        try{{
            const res = await fetch('/api/news?cat='+encodeURIComponent(currentCat));
            const news = await res.json();
            const container = document.getElementById('newsContainer');
            let html = '';
            news.forEach((n,i)=>{{
                if(i==5) html += '<div class="card ad">مساحة إعلانية AdSense</div>';
                const badge = n.is_custom? '<div class="custom-badge">خاص - شامي 🔥</div>' : '';
                const urgent = n.urgent? 'border:2px solid #d32f2f' : '';
                html += `<div class="card" style="position:relative;${{urgent}}">${{badge}}<img src="${{n.image}}" loading="lazy"><div class="body"><span>${{n.source}} | ${{n.time}}</span><h2><a href="${{n.link}}" target="_blank">${{n.title}}</a></h2><div class="btns"><a href="${{n.link}}" target="_blank" class="r">اقرأ ↗</a><a href="${{n.wa}}" target="_blank" class="w">واتساب</a></div></div></div>`;
            }});
            container.innerHTML = html;
            document.getElementById('lastUpdate').innerText = 'آخر تحديث: '+new Date().toLocaleTimeString('ar-EG')+' - يتحدث كل دقيقة ✅';
        }}catch(e){{console.log('update failed',e)}}
    }}
    setInterval(refreshNews, 60000); // كل 60 ثانية
    console.log('⏰ التحديث التلقائي شغال كل دقيقة');
    </script></body></html>"""

if __name__=='__main__': app.run(host='0.0.0.0', port=10000)
