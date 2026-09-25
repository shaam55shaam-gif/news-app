from flask import Flask, request, Response, redirect, session, jsonify
import feedparser, urllib.parse, json, re, os
from datetime import datetime

app = Flask(__name__)
app.secret_key = "shami_final_v3"

FEEDS = {
    "الكل": "https://news.google.com/rss?hl=ar&gl=SA&ceid=SA:ar",
    "عاجل 🔴": "https://news.google.com/rss/search?q=عاجل&hl=ar&gl=SA&ceid=SA:ar",
    "رياضة ⚽": "https://news.google.com/rss/search?q=رياضة&hl=ar&gl=SA&ceid=SA:ar",
    "اقتصاد 💰": "https://news.google.com/rss/search?q=اقتصاد&hl=ar&gl=SA&ceid=SA:ar",
    "سياسة 🏛️": "https://news.google.com/rss/search?q=سياسة&hl=ar&gl=SA&ceid=SA:ar",
    "ثقافية 🎭": "https://news.google.com/rss/search?q=ثقافة+فن&hl=ar&gl=SA&ceid=SA:ar"
}

# مصادر إضافية احتياطية - خفيفة
BACKUP_FEEDS = {
    "الكل": "https://feeds.bbci.co.uk/arabic/rss.xml",
    "عاجل 🔴": "https://www.alarabiya.net/.mrss/ar.xml",
    "رياضة ⚽": "https://www.yallakora.com/rss",
    "اقتصاد 💰": "https://www.alarabiya.net/.mrss/ar/business.xml",
    "سياسة 🏛️": "https://feeds.bbci.co.uk/arabic/topics/مصر/rss.xml",
    "ثقافية 🎭": "https://news.google.com/rss/search?q=افلام+مسلسلات&hl=ar&gl=SA&ceid=SA:ar"
}

CUSTOM_FILE = "custom_news.json"
CUSTOM_NEWS = []
if os.path.exists(CUSTOM_FILE):
    try: CUSTOM_NEWS = json.load(open(CUSTOM_FILE, encoding="utf-8"))
    except: pass

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
    cf = [n for n in CUSTOM_NEWS if cat == "الكل" or n.get("category")==cat]
    all_news = []
    # جرب المصدر الأساسي
    try:
        feed = feedparser.parse(FEEDS.get(cat, FEEDS["الكل"]))
        for e in feed.entries[:15]:
            all_news.append({"title":e.title,"link":e.link,"time":getattr(e,'published','')[:16] or datetime.now().strftime("%H:%M"),"source":"Google","image":get_image(e),"wa":f"https://wa.me/?text={urllib.parse.quote(e.title)}","is_custom":False})
    except: pass

    # إذا قليل، زود من الاحتياطي - مصدر واحد بس مشان ما يعلق
    if len(all_news) < 5:
        try:
            feed2 = feedparser.parse(BACKUP_FEEDS.get(cat, BACKUP_FEEDS["الكل"]))
            for e in feed2.entries[:10]:
                all_news.append({"title":e.title,"link":e.link,"time":getattr(e,'published','')[:16] or datetime.now().strftime("%H:%M"),"source":"مصدر إضافي","image":get_image(e),"wa":f"https://wa.me/?text={urllib.parse.quote(e.title)}","is_custom":False})
        except: pass

    if not all_news and not cf:
        return [{"title": f"جاري تحديث أخبار {cat} - انتظر دقيقة","link":"#","time":datetime.now().strftime("%H:%M"),"source":"شامي","image":"https://images.unsplash.com/photo-1504711434969-e33886168f5c?w=600","wa":"#","is_custom":False}]

    return cf + all_news[:20]

@app.route('/api/news')
def api_news():
    return jsonify(get_news(request.args.get('cat','الكل')))

@app.route('/manifest.json')
def manifest():
    data = {"name":"أخبار شامي","short_name":"شامي نيوز","start_url":"/","display":"standalone","background_color":"#b71c1c","theme_color":"#b71c1c","lang":"ar","dir":"rtl","icons":[{"src":"https://cdn-icons-png.flaticon.com/512/21/21601.png","sizes":"192x192","type":"image/png"}]}
    return Response(json.dumps(data, ensure_ascii=False), mimetype='application/manifest+json')

@app.route('/sw.js')
def sw():
    return Response("self.addEventListener('install',e=>self.skipWaiting());", mimetype='application/javascript')

ADMIN_PASSWORD = "shami123"
@app.route('/admin', methods=['GET','POST'])
def admin():
    if request.args.get('logout'):
        session.pop('admin', None)
        return redirect('/admin')
    if request.method == 'POST':
        if request.form.get('password'):
            if request.form.get('password') == ADMIN_PASSWORD: session['admin'] = True
            else: return "<h2>غلط</h2><a href='/admin'>رجوع</a>"
        elif session.get('admin') and request.form.get('title'):
            CUSTOM_NEWS.insert(0, {"title":request.form.get('title'),"link":request.form.get('link') or "#","time":datetime.now().strftime("%H:%M"),"source":"خاص - شامي 🔥","image":request.form.get('image') or "https://images.unsplash.com/photo-1504711434969-e33886168f5c?w=600","wa":f"https://wa.me/?text={urllib.parse.quote(request.form.get('title'))}","is_custom":True,"category":request.form.get('category','الكل')})
            save_custom()
        elif request.form.get('delete_index') is not None:
            try: CUSTOM_NEWS.pop(int(request.form.get('delete_index'))); save_custom()
            except: pass
    if not session.get('admin'):
        return """<!doctype html><html dir=rtl><head><meta charset=utf-8><meta name=viewport content=width=device-width,initial-scale=1><style>body{font-family:Tahoma;background:#f0f2f5;display:flex;justify-content:center;align-items:center;height:100vh;margin:0}.box{background:#fff;padding:30px;border-radius:12px;width:320px;text-align:center}input{width:100%;padding:12px;margin:8px 0}button{width:100%;padding:12px;background:#b71c1c;color:#fff;border:0;border-radius:8px}</style></head><body><form class=box method=post><h2>🔐 شامي</h2><input type=password name=password placeholder=shami123 required><button>دخول</button></form></body></html>"""
    lst="".join([f'<div style="background:#fff;padding:8px;margin:6px 0;border-radius:8px;display:flex;justify-content:space-between"><span>{n["title"][:35]}</span><form method=post><input type=hidden name=delete_index value={i}><button style="background:red;color:#fff;border:0;padding:4px 8px;border-radius:6px">حذف</button></form></div>' for i,n in enumerate(CUSTOM_NEWS)])
    return f"""<!doctype html><html dir=rtl><head><meta charset=utf-8><meta name=viewport content=width=device-width,initial-scale=1><style>body{{font-family:Tahoma;background:#f0f2f5;margin:0}}.h{{background:#b71c1c;color:#fff;padding:14px;text-align:center}}.c{{max-width:600px;margin:auto;padding:12px}}input,select{{width:100%;padding:10px;margin:5px 0}}.btn{{width:100%;background:#b71c1c;color:#fff;padding:10px;border:0;border-radius:8px}}</style></head><body><div class=h><h2>لوحة تحكم</h2><a href=/ style=color:#fff>موقع</a> | <a href=/admin?logout=1 style=color:#ffcccb>خروج</a></div><div class=c><form method=post style=background:#fff;padding:12px;border-radius:12px><input name=title placeholder="عنوان *" required><input name=image placeholder="رابط صورة"><input name=link placeholder="رابط"><select name=category><option>الكل</option><option>عاجل 🔴</option><option>رياضة ⚽</option><option>اقتصاد 💰</option><option>سياسة 🏛️</option><option>ثقافية 🎭</option></select><button class=btn>نشر</button></form><h3>أخبارك ({len(CUSTOM_NEWS)}):</h3>{lst}</div></body></html>"""

@app.route('/')
def home():
    cat = request.args.get('cat','الكل')
    news = get_news(cat)
    tabs = "".join([f'<a href="/?cat={urllib.parse.quote(k)}" class="tab {"active" if k==cat else ""}">{k}</a>' for k in FEEDS])
    cards=""
    for i,n in enumerate(news):
        if i==5: cards+='<div class="card ad">مساحة إعلانية AdSense</div>'
        badge = '<div style="background:#b71c1c;color:#fff;padding:4px 8px;font-size:11px;position:absolute;top:0;right:0">خاص 🔥</div>' if n.get('is_custom') else ''
        cards+=f'<div class="card" style="position:relative">{badge}<img src="{n["image"]}" loading="lazy"><div class="body"><span>{n["source"]} | {n["time"]}</span><h2><a href="{n["link"]}" target="_blank">{n["title"]}</a></h2><div class="btns"><a href="{n["link"]}" target="_blank" class="r">اقرأ</a><a href="{n["wa"]}" target="_blank" class="w">واتساب</a></div></div></div>'
    return f"""<!doctype html><html dir="rtl" lang="ar"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>أخبار شامي</title><link rel="manifest" href="/manifest.json"><meta name="theme-color" content="#b71c1c">
    <style>*{{box-sizing:border-box}}body{{margin:0;font-family:Tahoma;background:#f0f2f5}}.h{{background:#b71c1c;color:#fff;padding:14px;display:flex;justify-content:space-between;align-items:center;position:sticky;top:0;z-index:10}}.tabs{{display:flex;gap:8px;overflow:auto;padding:10px;background:#fff;position:sticky;top:60px}}.tab{{padding:8px 14px;background:#eee;border-radius:20px;text-decoration:none;color:#333;white-space:nowrap}}.tab.active{{background:#d32f2f;color:#fff}}.c{{max-width:700px;margin:auto;padding:10px}}.card{{background:#fff;border-radius:12px;overflow:hidden;margin:12px 0}}.card img{{width:100%;height:200px;object-fit:cover}}.body{{padding:12px}}.btns{{display:flex;gap:8px}}.r,.w{{flex:1;text-align:center;padding:10px;border-radius:8px;color:#fff;font-weight:bold}}.r{{background:#111}}.w{{background:#25D366}}.live{{width:8px;height:8px;background:#0f0;border-radius:50%;display:inline-block;animation:p 1s infinite}}@keyframes p{{0%{{opacity:1}}50%{{opacity:.3}}100%{{opacity:1}}}}#upd{{font-size:11px;opacity:.7}}</style></head>
    <body><div class="h"><div><h1 style="margin:0;font-size:18px">🔥 شامي <span class="live"></span></h1><div id="upd">يتحدث كل دقيقة</div></div><button onclick="document.body.classList.toggle('dark')" style="background:rgba(255,255,255,.2);border:0;color:#fff;padding:6px 10px;border-radius:20px">🌙</button></div><div class="tabs">{tabs}</div><div class="c" id="newsContainer">{cards}</div>
    <script>
    const curCat = new URLSearchParams(window.location.search).get('cat') || 'الكل';
    async function refreshNews(){{
        try{{
            const res = await fetch('/api/news?cat='+encodeURIComponent(curCat));
            const news = await res.json();
            let html='';
            news.forEach((n,i)=>{{
                if(i==5) html+='<div class="card ad">مساحة إعلانية</div>';
                const badge=n.is_custom?'<div style="background:#b71c1c;color:#fff;padding:4px 8px;font-size:11px;position:absolute;top:0;right:0">خاص 🔥</div>':'';
                html+=`<div class="card" style="position:relative">${{badge}}<img src="${{n.image}}"><div class="body"><span>${{n.source}} | ${{n.time}}</span><h2><a href="${{n.link}}" target="_blank">${{n.title}}</a></h2><div class="btns"><a href="${{n.link}}" target="_blank" class="r">اقرأ</a><a href="${{n.wa}}" target="_blank" class="w">واتساب</a></div></div></div>`;
            }});
            document.getElementById('newsContainer').innerHTML=html;
            document.getElementById('upd').innerText='آخر تحديث: '+new Date().toLocaleTimeString('ar-EG')+' ✅';
        }}catch(e){{}}
    }}
    setInterval(refreshNews, 60000);
    if('serviceWorker' in navigator){{navigator.serviceWorker.register('/sw.js')}}
    </script></body></html>"""

if __name__=='__main__': app.run(host='0.0.0.0', port=10000)
