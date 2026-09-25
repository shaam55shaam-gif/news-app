from flask import Flask, request, Response, redirect, session, jsonify
import feedparser, urllib.parse, json, re, os, requests
from datetime import datetime

app = Flask(__name__)
app.secret_key = "shami_sport_pro"

FEEDS = {
    "الكل": "https://news.google.com/rss/search?q=سوريا&hl=ar&gl=SA&ceid=SA:ar",
    "عاجل 🔴": "https://news.google.com/rss/search?q=عاجل+سوريا&hl=ar&gl=SA&ceid=SA:ar",
    "رياضة ⚽": "https://news.google.com/rss/search?q=رياضة+سورية+الدوري+السوري&hl=ar&gl=SA&ceid=SA:ar",
    "اقتصاد 💰": "https://news.google.com/rss/search?q=اقتصاد&hl=ar&gl=SA&ceid=SA:ar",
    "سياسة 🏛️": "https://news.google.com/rss/search?q=سياسة+سوريا&hl=ar&gl=SA&ceid=SA:ar",
    "ثقافية 🎭": "https://news.google.com/rss/search?q=ثقافة&hl=ar&gl=SA&ceid=SA:ar",
    "فن 🎨": "https://news.google.com/rss/search?q=فن+مشاهير&hl=ar&gl=SA&ceid=SA:ar"
}

# مصادر الرياضة المنظمة قسم قسم
SPORTS_SOURCES = [
    # سورية 🇸🇾
    {"url": "https://sana.sy/feed/", "name": "سانا - رياضة 🇸🇾"},
    {"url": "https://www.efasport.com/feed/", "name": "الاتحاد السوري لكرة القدم 🇸🇾"},
    # عربية - دوريات عربية
    {"url": "https://www.kooora.com/rss/rss.html", "name": "كووورة - دوريات عربية ⚽"},
    {"url": "https://www.yallakora.com/rss/rss.aspx", "name": "يلا كورة - مصر والسعودية ⚽"},
    {"url": "https://www.filgoal.com/rss", "name": "فيلجول - الدوري المصري 🏆"},
    # عالمية - دوريات عالمية
    {"url": "https://www.beinsports.com/ar/rss", "name": "beIN Sports - دوريات عالمية 🌍"},
    {"url": "https://www.goal.com/ar/rss", "name": "Goal - أوروبا 🌍"},
    {"url": "https://arabic.cnn.com/api/v1/rss/rss.xml", "name": "CNN رياضة 🌍"},
    # Google إضافي للبطولات
    {"url": "https://news.google.com/rss/search?q=الدوري+الانجليزي+الاسباني+ابطال+اوروبا&hl=ar&gl=SA&ceid=SA:ar", "name": "بطولات عالمية 🏆"},
    {"url": "https://news.google.com/rss/search?q=الدوري+السعودي+المصري+السوري+ابطال+اسيا&hl=ar&gl=SA&ceid=SA:ar", "name": "بطولات عربية وسورية 🏆"},
]

EXTRA_FEEDS = {
    "الكل": ["https://sana.sy/feed/", "https://www.bbc.com/arabic/index.xml"],
    "عاجل 🔴": ["https://sana.sy/feed/"],
    "رياضة ⚽": SPORTS_SOURCES, # مصادر الرياضة الخاصة المنظمة
    "اقتصاد 💰": ["https://www.aljazeera.net/xml/rss/all.xml"],
    "سياسة 🏛️": ["https://www.bbc.com/arabic/index.xml", "https://sana.sy/feed/"],
    "ثقافية 🎭": ["https://sana.sy/feed/"],
    "فن 🎨": ["https://www.snacksyrian.com/feed/"]
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
    return "https://images.unsplash.com/photo-1461896836934-ffe607ba8211?w=600"

def get_news(cat):
    cf = [n for n in CUSTOM_NEWS if cat == "الكل" or n.get("category")==cat]
    all_news = []
    try:
        feed = feedparser.parse(FEEDS.get(cat, FEEDS["الكل"]))
        for e in feed.entries[:6]:
            all_news.append({"title":e.title,"link":e.link,"time":getattr(e,'published','')[:16] or datetime.now().strftime("%H:%M"),"source":"Google ⚽","image":get_image(e),"wa":f"https://wa.me/?text={urllib.parse.quote(e.title)}","is_custom":False})
    except: pass

    sources_to_fetch = EXTRA_FEEDS.get(cat, [])
    if cat == "رياضة ⚽":
        # للرياضة نجيب من كل المصادر المنظمة
        for src in sources_to_fetch:
            try:
                url = src["url"] if isinstance(src, dict) else src
                name = src["name"] if isinstance(src, dict) else "رياضة ⚽"
                feed2 = feedparser.parse(url)
                for e in feed2.entries[:3]:
                    all_news.append({"title":e.title,"link":e.link,"time":getattr(e,'published','')[:16],"source":name,"image":get_image(e),"wa":f"https://wa.me/?text={urllib.parse.quote(e.title)}","is_custom":False})
            except: continue
    else:
        for url in sources_to_fetch[:2]:
            try:
                feed2 = feedparser.parse(url)
                for e in feed2.entries[:3]:
                    all_news.append({"title":e.title,"link":e.link,"time":getattr(e,'published','')[:16],"source":"مصدر 🇸🇾","image":get_image(e),"wa":f"https://wa.me/?text={urllib.parse.quote(e.title)}","is_custom":False})
            except: continue

    if not all_news and not cf:
        return [{"title":f"جاري تحديث {cat}","link":"#","time":datetime.now().strftime("%H:%M"),"source":"شامي","image":"https://images.unsplash.com/photo-1461896836934-ffe607ba8211?w=600","wa":"#","is_custom":False}]
    return cf + all_news[:30]

@app.route('/read')
def read_article():
    url = request.args.get('url',''); title = request.args.get('title','خبر'); img = request.args.get('img','')
    if not url or url == "#": return redirect('/')
    article_text=""
    try:
        r = requests.get(url, headers={'User-Agent':'Mozilla/5.0'}, timeout=6)
        paragraphs = re.findall(r'<p[^>]*>(.*?)</p>', r.text, re.DOTALL)
        clean_paras=[]
        for p in paragraphs[:25]:
            clean = re.sub(r'<[^>]+>', '', p).strip()
            if len(clean) > 50: clean_paras.append(clean)
        article_text = "\n".join(clean_paras) if clean_paras else "اضغط فتح المصدر"
    except: article_text = "المحتوى محمي - افتح المصدر"
    return f"""<!doctype html><html dir="rtl" lang="ar"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>{title[:50]}</title>
    <style>body{{margin:0;font-family:Tahoma;background:#f5f5f5}}.h{{background:#1b5e20;color:#fff;padding:12px;display:flex;gap:10px;align-items:center;position:sticky;top:0}}.h a{{color:#fff;text-decoration:none;background:rgba(255,255,255,.2);padding:6px 14px;border-radius:20px}}.c{{max-width:700px;margin:auto;background:#fff}}.c img{{width:100%;max-height:360px;object-fit:cover}}.body{{padding:18px}}.body h1{{font-size:21px;line-height:1.5}}.body p{{font-size:17px;line-height:1.9;margin:14px 0}}.acts{{display:flex;gap:10px;padding:16px;position:sticky;bottom:0;background:#fff;border-top:1px solid #eee}}.btn{{flex:1;padding:12px;text-align:center;border-radius:10px;text-decoration:none;font-weight:bold}}.src{{background:#111;color:#fff}}.wa{{background:#25D366;color:#fff}}</style></head>
    <body><div class="h"><a href="javascript:history.back()">← رجوع</a><b>رياضة ⚽</b></div><div class="c"><img src="{img}" onerror="this.style.display='none'"><div class="body"><h1>{title}</h1><hr>{"".join([f'<p>{p}</p>' for p in article_text.split(chr(10)) if p.strip()])}</div><div class="acts"><a href="{url}" target="_blank" class="btn src">فتح المصدر ↗</a><a href="https://wa.me/?text={urllib.parse.quote(title+' '+url)}" target="_blank" class="btn wa">واتساب</a></div></div></body></html>"""

@app.route('/api/news')
def api_news(): return jsonify(get_news(request.args.get('cat','الكل')))
@app.route('/manifest.json')
def manifest():
    d={"name":"أخبار شامي","short_name":"شامي","start_url":"/","display":"standalone","background_color":"#1b5e20","theme_color":"#1b5e20","lang":"ar","dir":"rtl","icons":[{"src":"https://cdn-icons-png.flaticon.com/512/21/21601.png","sizes":"192x192","type":"image/png"}]}
    return Response(json.dumps(d, ensure_ascii=False), mimetype='application/manifest+json')
@app.route('/sw.js')
def sw(): return Response("self.addEventListener('install',e=>self.skipWaiting());", mimetype='application/javascript')
ADMIN_PASSWORD="shami123"
@app.route('/admin', methods=['GET','POST'])
def admin():
    if request.args.get('logout'): session.pop('admin',None); return redirect('/admin')
    if request.method=='POST':
        if request.form.get('password') and request.form.get('password')==ADMIN_PASSWORD: session['admin']=True
        elif session.get('admin') and request.form.get('title'):
            CUSTOM_NEWS.insert(0, {"title":request.form.get('title'),"link":request.form.get('link') or "#","time":datetime.now().strftime("%H:%M"),"source":"خاص 🔥","image":request.form.get('image') or "https://images.unsplash.com/photo-1461896836934-ffe607ba8211?w=600","wa":f"https://wa.me/?text={urllib.parse.quote(request.form.get('title'))}","is_custom":True,"category":request.form.get('category','الكل')})
            save_custom()
        elif request.form.get('delete_index') is not None:
            try: CUSTOM_NEWS.pop(int(request.form.get('delete_index'))); save_custom()
            except: pass
    if not session.get('admin'):
        return """<!doctype html><html dir=rtl><head><meta charset=utf-8><meta name=viewport content=width=device-width,initial-scale=1><style>body{font-family:Tahoma;background:#f0f2f5;display:flex;justify-content:center;align-items:center;height:100vh;margin:0}.box{background:#fff;padding:30px;border-radius:12px;width:320px;text-align:center}input{width:100%;padding:12px;margin:8px 0}button{width:100%;padding:12px;background:#1b5e20;color:#fff;border:0;border-radius:8px}</style></head><body><form class=box method=post><h2>🔐 شامي رياضة</h2><input type=password name=password placeholder=shami123 required><button>دخول</button></form></body></html>"""
    lst="".join([f'<div style="background:#fff;padding:8px;margin:6px 0;display:flex;justify-content:space-between"><span>{n["title"][:30]}</span><form method=post><input type=hidden name=delete_index value={i}><button style="background:red;color:#fff;border:0;padding:4px 8px">حذف</button></form></div>' for i,n in enumerate(CUSTOM_NEWS)])
    return f"""<!doctype html><html dir=rtl><head><meta charset=utf-8><meta name=viewport content=width=device-width,initial-scale=1><style>body{{font-family:Tahoma;background:#f0f2f5;margin:0}}.h{{background:#1b5e20;color:#fff;padding:14px;text-align:center}}.c{{max-width:600px;margin:auto;padding:12px}}input,select{{width:100%;padding:10px;margin:5px 0}}.btn{{width:100%;background:#1b5e20;color:#fff;padding:10px;border:0;border-radius:8px}}</style></head><body><div class=h><h2>لوحة تحكم - رياضة ⚽ منظم</h2><a href=/ style=color:#fff>موقع</a></div><div class=c><form method=post style=background:#fff;padding:12px;border-radius:12px><input name=title placeholder="عنوان رياضي *" required><input name=image placeholder="صورة"><input name=link placeholder="رابط"><select name=category><option>رياضة ⚽</option><option>الكل</option><option>عاجل 🔴</option></select><button class=btn>نشر</button></form>{lst}<div style=background:#fff;padding:12px;margin-top:12px><b>مصادر الرياضة الحالية:</b><br>{"<br>".join([f"✅ {s['name']}" for s in SPORTS_SOURCES])}</div></div></body></html>"""

@app.route('/')
def home():
    cat=request.args.get('cat','الكل')
    news=get_news(cat)
    tabs="".join([f'<a href="/?cat={urllib.parse.quote(k)}" class="tab {"active" if k==cat else ""}">{k}</a>' for k in FEEDS])
    cards=""
    for i,n in enumerate(news):
        if i==5: cards+='<div class="card" style="background:#fff9c4;padding:12px;text-align:center;border:2px dashed #fbc02d">إعلان - مساحة إعلانية</div>'
        read_url=f"/read?url={urllib.parse.quote(n['link'])}&title={urllib.parse.quote(n['title'])}&img={urllib.parse.quote(n['image'])}"
        cards+=f'<div class="card"><img src="{n["image"]}" loading="lazy"><div class="body"><span>{n["source"]} | {n["time"]}</span><h2>{n["title"]}</h2><div class="btns"><a href="{read_url}" class="r">📖 اقرأ</a><a href="{n["wa"]}" target="_blank" class="w">واتساب</a></div></div></div>'
    sport_banner = '<div style="background:#1b5e20;color:#fff;padding:10px;text-align:center;font-size:13px">⚽ مصادر منظمة: سورية 🇸🇾 | عربية 🏆 | عالمية 🌍 | بطولات ودوريات</div>' if cat=='رياضة ⚽' else ''
    return f"""<!doctype html><html dir="rtl"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>شامي - رياضة منظمة</title><link rel="manifest" href="/manifest.json"><style>body{{margin:0;font-family:Tahoma;background:#f0f2f5}}.h{{background:#1b5e20;color:#fff;padding:12px;display:flex;justify-content:space-between;position:sticky;top:0;z-index:10}}.tabs{{display:flex;gap:8px;overflow:auto;padding:10px;background:#fff;position:sticky;top:56px}}.tab{{padding:8px 14px;background:#eee;border-radius:20px;text-decoration:none;color:#333;white-space:nowrap;font-size:13px}}.tab.active{{background:#2e7d32;color:#fff}}.c{{max-width:700px;margin:auto;padding:10px}}.card{{background:#fff;border-radius:12px;overflow:hidden;margin:12px 0}}.card img{{width:100%;height:190px;object-fit:cover}}.body{{padding:12px}}.btns{{display:flex;gap:8px}}.r,.w{{flex:1;text-align:center;padding:10px;border-radius:8px;color:#fff;font-weight:bold;text-decoration:none}}.r{{background:#111}}.w{{background:#25D366}} #upd{{font-size:11px;opacity:.8}}</style></head>
    <body><div class="h"><div><h1 style="margin:0;font-size:17px">🔥 شامي - رياضة منظمة ⚽</h1><div id="upd">دوريات عالمية + عربية + سورية</div></div><a href="/admin" style="color:#fff;text-decoration:none">⚙️</a></div><div class="tabs">{tabs}</div>{sport_banner}<div class="c" id="newsContainer">{cards}</div>
    <script>
    const curCat = new URLSearchParams(window.location.search).get('cat') || 'الكل';
    async function refreshNews(){{
        try{{
            const res = await fetch('/api/news?cat='+encodeURIComponent(curCat));
            const news = await res.json();
            let html='';
            news.forEach((n,i)=>{{
                if(i==5) html+='<div class="card" style="background:#fff9c4;padding:12px;text-align:center;border:2px dashed #fbc02d">إعلان</div>';
                const readUrl = `/read?url=${{encodeURIComponent(n.link)}}&title=${{encodeURIComponent(n.title)}}&img=${{encodeURIComponent(n.image)}}`;
                html+=`<div class="card"><img src="${{n.image}}"><div class="body"><span>${{n.source}} | ${{n.time}}</span><h2>${{n.title}}</h2><div class="btns"><a href="${{readUrl}}" class="r">📖 اقرأ</a><a href="${{n.wa}}" target="_blank" class="w">واتساب</a></div></div></div>`;
            }});
            document.getElementById('newsContainer').innerHTML=html;
            document.getElementById('upd').innerText='آخر تحديث: '+new Date().toLocaleTimeString('ar-EG')+' ✅';
        }}catch(e){{}}
    }}
    setInterval(refreshNews, 60000);
    </script></body></html>"""

if __name__=='__main__': app.run(host='0.0.0.0', port=10000)
