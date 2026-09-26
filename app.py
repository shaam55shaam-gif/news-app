from flask import Flask, request, Response, redirect, session, jsonify
import feedparser, urllib.parse, json, re, os, time, concurrent.futures
from datetime import datetime

app = Flask(__name__)
app.secret_key = "shami_full_speed"

FEEDS = {
    "الكل": "https://news.google.com/rss/search?q=سوريا&hl=ar&gl=SA&ceid=SA:ar",
    "عاجل 🔴": "https://news.google.com/rss/search?q=عاجل+سوريا&hl=ar&gl=SA&ceid=SA:ar",
    "رياضة ⚽": "https://news.google.com/rss/search?q=رياضة+سورية&hl=ar&gl=SA&ceid=SA:ar",
    "اقتصاد 💰": "https://news.google.com/rss/search?q=اقتصاد+سوريا+دولار&hl=ar&gl=SA&ceid=SA:ar",
    "سياسة 🏛️": "https://news.google.com/rss/search?q=سياسة+سوريا&hl=ar&gl=SA&ceid=SA:ar",
    "ثقافية 🎭": "https://news.google.com/rss/search?q=ثقافة+سوريا&hl=ar&gl=SA&ceid=SA:ar",
    "فن 🎨": "https://news.google.com/rss/search?q=فن+مشاهير+سوريا&hl=ar&gl=SA&ceid=SA:ar"
}

# === كل المصادر كاملة بدون حذف ===
SPORTS_SOURCES = [
    {"url": "https://www.yallakora.com/rss/rss.aspx", "name": "يلا كورة ⚽"},
    {"url": "https://www.beinsports.com/ar/rss", "name": "beIN 🌍"},
    {"url": "https://sana.sy/feed/", "name": "سانا رياضة 🇸🇾"},
    {"url": "https://www.kooora.com/rss.aspx", "name": "كووورة ⚽"},
    {"url": "https://www.goal.com/ar/rss", "name": "Goal ⚽"},
    {"url": "https://www.filgoal.com/rss", "name": "فيلجول 🇪🇬"},
]

POLITICS_SOURCES = [
    {"url": "https://www.bbc.com/arabic/index.xml", "name": "BBC 🌍"},
    {"url": "https://www.aljazeera.net/xml/rss/all.xml", "name": "الجزيرة 🌍"},
    {"url": "https://sana.sy/feed/", "name": "سانا سياسة 🇸🇾"},
    {"url": "https://www.skynewsarabia.com/web/rss", "name": "سكاي نيوز 🌍"},
    {"url": "https://arabic.cnn.com/rss", "name": "CNN عربي 🌍"},
    {"url": "https://www.france24.com/ar/rss", "name": "فرانس 24 🌍"},
]

ECONOMY_SOURCES = [
    {"url": "https://www.aljazeera.net/xml/rss/all.xml", "name": "الجزيرة 💰"},
    {"url": "https://sana.sy/feed/", "name": "سانا اقتصاد 🇸🇾"},
    {"url": "https://www.skynewsarabia.com/web/rss", "name": "سكاي اقتصاد 💰"},
]

EXTRA_FEEDS = {
    "الكل": POLITICS_SOURCES[:2] + SPORTS_SOURCES[:1],
    "عاجل 🔴": POLITICS_SOURCES[:3],
    "رياضة ⚽": SPORTS_SOURCES,
    "سياسة 🏛️": POLITICS_SOURCES,
    "اقتصاد 💰": ECONOMY_SOURCES,
    "ثقافية 🎭": [{"url": "https://sana.sy/feed/", "name": "سانا ثقافة"}],
    "فن 🎨": [{"url": "https://www.snacksyrian.com/feed/", "name": "سناك سوري"}]
}

CUSTOM_FILE = "custom_news.json"
CUSTOM_NEWS = []
if os.path.exists(CUSTOM_FILE):
    try: CUSTOM_NEWS = json.load(open(CUSTOM_FILE, encoding="utf-8"))
    except: pass

def save_custom():
    try: json.dump(CUSTOM_NEWS, open(CUSTOM_FILE,"w",encoding="utf-8"), ensure_ascii=False, indent=2)
    except: pass

DEFAULT_IMAGES = {
    "الكل": "https://images.unsplash.com/photo-1504711434969-e33886168f5c?w=600",
    "عاجل 🔴": "https://images.unsplash.com/photo-1586339949916-3e9457bef6d3?w=600",
    "رياضة ⚽": "https://images.unsplash.com/photo-1461896836934-ffe607ba8211?w=600",
    "اقتصاد 💰": "https://images.unsplash.com/photo-1611974789855-9c2a0a7236a3?w=600",
    "سياسة 🏛️": "https://images.unsplash.com/photo-1529107386315-e1a2ed48a620?w=600",
    "ثقافية 🎭": "https://images.unsplash.com/photo-1513364776144-60967b0f800f?w=600",
    "فن 🎨": "https://images.unsplash.com/photo-1493225457124-a3eb161ffa5f?w=600",
}

def get_image(entry, cat="الكل"):
    try:
        if hasattr(entry, 'media_content') and entry.media_content:
            u = entry.media_content[0].get('url','')
            if u.startswith('http'): return u
        if hasattr(entry, 'media_thumbnail') and entry.media_thumbnail:
            u = entry.media_thumbnail[0].get('url','')
            if u.startswith('http'): return u
    except: pass
    m = re.search(r'<img[^>]+src="([^"]+)"', getattr(entry, 'description',''))
    if m and m.group(1).startswith('http'): return m.group(1)
    return DEFAULT_IMAGES.get(cat, DEFAULT_IMAGES["الكل"])

CACHE = {}
CACHE_TIME = {}

def fetch_one(args):
    src, cat = args
    try:
        f = feedparser.parse(src["url"])
        res=[]
        for e in f.entries[:3]:
            res.append({"title":e.title,"link":e.link,"time":getattr(e,'published','')[:16] or datetime.now().strftime("%H:%M"),"source":src["name"],"image":get_image(e, cat),"wa":f"https://wa.me/?text={urllib.parse.quote(e.title)}","is_custom":False})
        return res
    except:
        return []

def get_news(cat, query=None):
    now = time.time()
    key = f"{cat}_{query or ''}"
    if key in CACHE and now - CACHE_TIME.get(key,0) < 180:
        cf = [n for n in CUSTOM_NEWS if cat == "الكل" or n.get("category")==cat] if not query else []
        return cf + CACHE[key]

    if query:
        try:
            feed = feedparser.parse(f"https://news.google.com/rss/search?q={urllib.parse.quote(query)}&hl=ar&gl=SA&ceid=SA:ar")
            res=[{"title":e.title,"link":e.link,"time":getattr(e,'published','')[:16],"source":"بحث 🔍","image":get_image(e, cat),"wa":f"https://wa.me/?text={urllib.parse.quote(e.title)}","is_custom":False} for e in feed.entries[:20]]
            CACHE[key]=res
            CACHE_TIME[key]=now
            return res
        except:
            return []

    cf = [n for n in CUSTOM_NEWS if cat == "الكل" or n.get("category")==cat]
    all_news=[]
    # Google خبرين بس
    try:
        fg = feedparser.parse(FEEDS.get(cat))
        for e in fg.entries[:2]:
            all_news.append({"title":e.title,"link":e.link,"time":getattr(e,'published','')[:16] or datetime.now().strftime("%H:%M"),"source":"Google","image":get_image(e, cat),"wa":f"https://wa.me/?text={urllib.parse.quote(e.title)}","is_custom":False})
    except: pass

    # مصادر اضافية بشكل متوازي وسريع
    sources = EXTRA_FEEDS.get(cat, [])[:6]
    if sources:
        with concurrent.futures.ThreadPoolExecutor(max_workers=6) as ex:
            results = list(ex.map(fetch_one, [(s, cat) for s in sources]))
            for r in results:
                all_news.extend(r)

    CACHE[key]=all_news[:30]
    CACHE_TIME[key]=now
    return cf + all_news[:30] if (cf or all_news) else [{"title":f"لا يوجد أخبار في {cat}","link":"#","time":datetime.now().strftime("%H:%M"),"source":"شامي","image":DEFAULT_IMAGES.get(cat),"wa":"#","is_custom":False}]

@app.route('/read')
def read_article():
    import requests
    url = request.args.get('url',''); title = request.args.get('title','خبر'); img = request.args.get('img','')
    if not url or url == "#": return redirect('/')
    txt="افتح المصدر"
    try:
        r = requests.get(url, headers={'User-Agent':'Mozilla/5.0'}, timeout=4)
        ps = re.findall(r'<p[^>]*>(.*?)</p>', r.text, re.DOTALL)
        clean=[re.sub(r'<[^>]+>', '', p).strip() for p in ps[:12] if len(re.sub(r'<[^>]+>', '', p).strip())>40]
        if clean: txt = "\n".join(clean)
    except: pass
    return f"""<!doctype html><html dir="rtl"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>{title[:50]}</title>
    <style>body{{margin:0;font-family:Tahoma;background:#f5f5f5}}.h{{background:#1b5e20;color:#fff;padding:12px;display:flex;gap:10px;position:sticky;top:0}}.h a{{color:#fff;text-decoration:none;background:rgba(255,255,255,.2);padding:6px 14px;border-radius:20px}}.c{{max-width:700px;margin:auto;background:#fff}}.c img{{width:100%}}.body{{padding:18px}}h1{{font-size:20px}}p{{font-size:17px;line-height:1.8;margin:12px 0}}.acts{{display:flex;gap:10px;padding:16px;position:sticky;bottom:0;background:#fff}}.btn{{flex:1;padding:12px;text-align:center;border-radius:10px;text-decoration:none;font-weight:bold}}.src{{background:#111;color:#fff}}.wa{{background:#25D366;color:#fff}}</style></head>
    <body><div class="h"><a href="javascript:history.back()">← رجوع</a><b>شامي</b></div><div class="c"><img src="{img}"><div class="body"><h1>{title}</h1><hr>{"".join([f'<p>{p}</p>' for p in txt.split(chr(10))])}</div><div class="acts"><a href="{url}" target="_blank" class="btn src">فتح المصدر ↗</a><a href="https://wa.me/?text={urllib.parse.quote(title+' '+url)}" class="btn wa">واتساب</a></div></div></body></html>"""

@app.route('/search')
def search():
    q=request.args.get('q','').strip()
    if not q: return redirect('/')
    news=get_news("الكل", query=q)
    return home_render("الكل", news, q)

def home_render(cat, news, q=None):
    tabs="".join([f'<a href="/?cat={urllib.parse.quote(k)}" class="tab {"active" if k==cat and not q else ""}">{k}</a>' for k in FEEDS])
    economy_bar='<div style="background:#0d2818;color:#fff;padding:10px 14px;display:flex;justify-content:space-between;font-size:13px;border-radius:10px;margin:10px"><span>💵 دمشق: ~15,200 ل.س</span><span>🪙 ذهب: 1.1M</span><span style="background:#25D366;padding:2px 8px;border-radius:10px">مباشر</span></div>'
    search_box=f'''
    <div style="background:#fff;padding:10px;position:sticky;top:56px;z-index:9;border-bottom:1px solid #eee">
      <form action="/search" method="get" style="display:flex;gap:8px;max-width:700px;margin:auto">
        <input name="q" value="{q or ''}" placeholder="🔍 ابحث: برشلونة، الدولار، سياسة..." style="flex:1;padding:10px 14px;border:1px solid #ddd;border-radius:20px;font-family:Tahoma">
        <button style="background:#1b5e20;color:#fff;border:0;padding:10px 18px;border-radius:20px;font-weight:bold">بحث</button>
      </form>
    </div>'''
    title_bar=f'<div style="padding:10px;background:#e8f5e9;text-align:center">نتائج "{q}" - {len(news)} خبر <a href="/" style="color:#1b5e20">✕</a></div>' if q else ""
    cards=""
    for i,n in enumerate(news):
        if not q and i==2: cards+=economy_bar
        read_url=f"/read?url={urllib.parse.quote(n['link'])}&title={urllib.parse.quote(n['title'])}&img={urllib.parse.quote(n['image'])}"
        cards+=f'<div class="card"><img src="{n["image"]}" loading="lazy" onerror="this.src=\'{DEFAULT_IMAGES.get(cat)}\'"><div class="body"><span>{n["source"]} | {n["time"]}</span><h2>{n["title"]}</h2><div class="btns"><a href="{read_url}" class="r">📖 اقرأ</a><a href="{n["wa"]}" target="_blank" class="w">واتساب</a></div></div></div>'
    return f"""<!doctype html><html dir="rtl"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>شامي</title><link rel="manifest" href="/manifest.json">
    <style>body{{margin:0;font-family:Tahoma;background:#f0f2f5}}.h{{background:#1b5e20;color:#fff;padding:12px;display:flex;justify-content:space-between;position:sticky;top:0;z-index:10}}.tabs{{display:flex;gap:8px;overflow:auto;padding:10px;background:#fff;position:sticky;top:105px}}.tab{{padding:8px 14px;background:#eee;border-radius:20px;text-decoration:none;color:#333;white-space:nowrap;font-size:13px}}.tab.active{{background:#2e7d32;color:#fff}}.c{{max-width:700px;margin:auto;padding:10px}}.card{{background:#fff;border-radius:12px;overflow:hidden;margin:12px 0}}.card img{{width:100%;height:190px;object-fit:cover}}.body{{padding:12px}}.btns{{display:flex;gap:8px}}.r,.w{{flex:1;text-align:center;padding:10px;border-radius:8px;color:#fff;font-weight:bold;text-decoration:none}}.r{{background:#111}}.w{{background:#25D366}}</style></head>
    <body><div class="h"><div><h1 style="margin:0;font-size:16px">🔥 شامي - كامل + مسرّع ✅</h1><div style="font-size:11px">{len(SPORTS_SOURCES)} رياضة + {len(POLITICS_SOURCES)} سياسة + بحث + صور حقيقية</div></div><a href="/admin" style="color:#fff;text-decoration:none">⚙️</a></div>{search_box}<div class="tabs">{tabs}</div>{title_bar}<div class="c">{cards}</div></body></html>"""

@app.route('/')
def home():
    cat=request.args.get('cat','الكل')
    return home_render(cat, get_news(cat))

@app.route('/manifest.json')
def manifest():
    d={"name":"شامي","short_name":"شامي","start_url":"/","display":"standalone","background_color":"#1b5e20","theme_color":"#1b5e20","lang":"ar","dir":"rtl","icons":[{"src":"https://cdn-icons-png.flaticon.com/512/21/21601.png","sizes":"192x192","type":"image/png"}]}
    return Response(json.dumps(d, ensure_ascii=False), mimetype='application/manifest+json')
@app.route('/sw.js')
def sw(): return Response("self.addEventListener('install',e=>self.skipWaiting());", mimetype='application/javascript')
ADMIN_PASSWORD="shami123"
@app.route('/admin', methods=['GET','POST'])
def admin():
    if request.args.get('logout'): session.pop('admin',None); return redirect('/admin')
    if request.method=='POST':
        if request.form.get('password')==ADMIN_PASSWORD: session['admin']=True
        elif session.get('admin') and request.form.get('title'):
            CUSTOM_NEWS.insert(0, {"title":request.form.get('title'),"link":request.form.get('link') or "#","time":datetime.now().strftime("%H:%M"),"source":"خاص 🔥","image":request.form.get('image') or DEFAULT_IMAGES.get(request.form.get('category','الكل')),"wa":f"https://wa.me/?text={urllib.parse.quote(request.form.get('title'))}","is_custom":True,"category":request.form.get('category','الكل')})
            save_custom()
        elif request.form.get('delete_index') is not None:
            try: CUSTOM_NEWS.pop(int(request.form.get('delete_index'))); save_custom()
            except: pass
    if not session.get('admin'):
        return """<!doctype html><html dir=rtl><head><meta charset=utf-8><meta name=viewport content="width=device-width,initial-scale=1><style>body{font-family:Tahoma;background:#f0f2f5;display:flex;justify-content:center;align-items:center;height:100vh;margin:0}.box{background:#fff;padding:30px;border-radius:12px;width:320px;text-align:center}input{width:100%;padding:12px;margin:8px 0}button{width:100%;padding:12px;background:#1b5e20;color:#fff;border:0;border-radius:8px}</style></head><body><form class=box method=post><h2>🔐 شامي</h2><input type=password name=password placeholder=shami123 required><button>دخول</button></form></body></html>"""
    lst="".join([f'<div style="background:#fff;padding:8px;margin:6px 0;display:flex;justify-content:space-between"><span>{n["title"][:30]}</span><form method=post><input type=hidden name=delete_index value={i}><button style="background:red;color:#fff;border:0;padding:4px 8px">حذف</button></form></div>' for i,n in enumerate(CUSTOM_NEWS)])
    return f"""<!doctype html><html dir=rtl><head><meta charset=utf-8><meta name=viewport content="width=device-width,initial-scale=1><style>body{{font-family:Tahoma;background:#f0f2f5;margin:0}}.h{{background:#1b5e20;color:#fff;padding:14px;text-align:center}}.c{{max-width:600px;margin:auto;padding:12px}}input,select{{width:100%;padding:10px;margin:5px 0}}.btn{{width:100%;background:#1b5e20;color:#fff;padding:10px;border:0;border-radius:8px}}</style></head><body><div class=h><h2>شامي كامل - كل المصادر ✅</h2></div><div class=c><form method=post style=background:#fff;padding:12px><input name=title placeholder="عنوان *" required><input name=image placeholder="صورة"><input name=link placeholder="رابط"><select name=category><option>سياسة 🏛️</option><option>رياضة ⚽</option><option>اقتصاد 💰</option><option>الكل</option></select><button class=btn>نشر</button></form>{lst}</div></body></html>"""

if __name__=='__main__':
    port = int(os.environ.get("PORT", 10000))
    app.run(host='0.0.0.0', port=port)
