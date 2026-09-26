from flask import Flask, request, Response, redirect, session, jsonify
import feedparser, urllib.parse, json, re, os, requests, time
from datetime import datetime

app = Flask(__name__)
app.secret_key = "shami_images_fixed"

FEEDS = {
    "الكل": "https://news.google.com/rss/search?q=سوريا&hl=ar&gl=SA&ceid=SA:ar",
    "عاجل 🔴": "https://news.google.com/rss/search?q=عاجل+سوريا&hl=ar&gl=SA&ceid=SA:ar",
    "رياضة ⚽": "https://news.google.com/rss/search?q=رياضة+سورية&hl=ar&gl=SA&ceid=SA:ar",
    "اقتصاد 💰": "https://news.google.com/rss/search?q=اقتصاد+سوريا&hl=ar&gl=SA&ceid=SA:ar",
    "سياسة 🏛️": "https://news.google.com/rss/search?q=سياسة+سوريا&hl=ar&gl=SA&ceid=SA:ar",
    "ثقافية 🎭": "https://news.google.com/rss/search?q=ثقافة+سوريا&hl=ar&gl=SA&ceid=SA:ar",
    "فن 🎨": "https://news.google.com/rss/search?q=فن+مشاهير+سوريا&hl=ar&gl=SA&ceid=SA:ar"
}

SPORTS_SOURCES = [
    {"url": "https://sana.sy/feed/", "name": "سانا 🇸🇾"},
    {"url": "https://www.yallakora.com/rss/rss.aspx", "name": "يلا كورة ⚽"},
    {"url": "https://www.filgoal.com/rss", "name": "فيلجول 🏆"},
    {"url": "https://www.beinsports.com/ar/rss", "name": "beIN 🌍"},
    {"url": "https://news.google.com/rss/search?q=الدوري+الانجليزي+الاسباني&hl=ar&gl=SA&ceid=SA:ar", "name": "دوريات عالمية 🏆"},
    {"url": "https://news.google.com/rss/search?q=الدوري+السعودي+السوري&hl=ar&gl=SA&ceid=SA:ar", "name": "دوريات عربية 🇸🇾"},
]

EXTRA_FEEDS = {
    "الكل": ["https://sana.sy/feed/"],
    "عاجل 🔴": ["https://sana.sy/feed/"],
    "رياضة ⚽": SPORTS_SOURCES,
    "اقتصاد 💰": ["https://www.aljazeera.net/xml/rss/all.xml"],
    "سياسة 🏛️": ["https://www.bbc.com/arabic/index.xml"],
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

# صور ثابتة حسب القسم - بدون قصاصات
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
    # حاول تجيب صورة حقيقية من الخبر
    try:
        if hasattr(entry, 'media_content') and entry.media_content:
            u = entry.media_content[0].get('url','')
            if u.startswith('http'): return u
    except: pass
    try:
        if hasattr(entry, 'media_thumbnail') and entry.media_thumbnail:
            u = entry.media_thumbnail[0].get('url','')
            if u.startswith('http'): return u
    except: pass
    try:
        if hasattr(entry, 'enclosures') and entry.enclosures:
            u = entry.enclosures[0].href
            if u.startswith('http'): return u
    except: pass
    m = re.search(r'<img[^>]+src="([^"]+)"', getattr(entry, 'description', ''))
    if m:
        u = m.group(1)
        if u.startswith('http'): return u
    # اذا ما في صورة - صورة مناسبة للقسم
    return DEFAULT_IMAGES.get(cat, DEFAULT_IMAGES["الكل"])

CACHE = {}
CACHE_TIME = {}

def get_news(cat):
    now = time.time()
    if cat in CACHE and now - CACHE_TIME.get(cat,0) < 180:
        cf = [n for n in CUSTOM_NEWS if cat == "الكل" or n.get("category")==cat]
        return cf + CACHE[cat]

    cf = [n for n in CUSTOM_NEWS if cat == "الكل" or n.get("category")==cat]
    all_news = []
    try:
        feed = feedparser.parse(FEEDS.get(cat))
        for e in feed.entries[:6]:
            all_news.append({"title":e.title,"link":e.link,"time":getattr(e,'published','')[:16] or datetime.now().strftime("%H:%M"),"source":"Google","image":get_image(e, cat),"wa":f"https://wa.me/?text={urllib.parse.quote(e.title)}","is_custom":False})
    except: pass
    for src in EXTRA_FEEDS.get(cat, [])[:4]:
        try:
            url = src["url"] if isinstance(src, dict) else src
            name = src["name"] if isinstance(src, dict) else "مصدر"
            f2 = feedparser.parse(url)
            for e in f2.entries[:2]:
                all_news.append({"title":e.title,"link":e.link,"time":getattr(e,'published','')[:16],"source":name,"image":get_image(e, cat),"wa":f"https://wa.me/?text={urllib.parse.quote(e.title)}","is_custom":False})
        except: continue

    CACHE[cat] = all_news[:25]
    CACHE_TIME[cat] = now
    return cf + all_news[:25] if (cf or all_news) else [{"title":f"لا يوجد أخبار في {cat} حاليا","link":"#","time":datetime.now().strftime("%H:%M"),"source":"شامي","image":DEFAULT_IMAGES.get(cat),"wa":"#","is_custom":False}]

@app.route('/read')
def read_article():
    url = request.args.get('url',''); title = request.args.get('title','خبر'); img = request.args.get('img','')
    if not url or url == "#": return redirect('/')
    txt="افتح المصدر لقراءة كامل الخبر"
    try:
        r = requests.get(url, headers={'User-Agent':'Mozilla/5.0'}, timeout=5)
        ps = re.findall(r'<p[^>]*>(.*?)</p>', r.text, re.DOTALL)
        clean=[re.sub(r'<[^>]+>', '', p).strip() for p in ps[:15] if len(re.sub(r'<[^>]+>', '', p).strip())>40]
        if clean: txt = "\n".join(clean)
    except: pass
    return f"""<!doctype html><html dir="rtl"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>{title[:50]}</title>
    <style>body{{margin:0;font-family:Tahoma;background:#f5f5f5}}.h{{background:#1b5e20;color:#fff;padding:12px;display:flex;gap:10px;position:sticky;top:0}}.h a{{color:#fff;text-decoration:none;background:rgba(255,255,255,.2);padding:6px 14px;border-radius:20px}}.c{{max-width:700px;margin:auto;background:#fff}}.c img{{width:100%;max-height:400px;object-fit:cover}}.body{{padding:18px}}h1{{font-size:20px}}p{{font-size:17px;line-height:1.8;margin:12px 0}}.acts{{display:flex;gap:10px;padding:16px;position:sticky;bottom:0;background:#fff;border-top:1px solid #eee}}.btn{{flex:1;padding:12px;text-align:center;border-radius:10px;text-decoration:none;font-weight:bold}}.src{{background:#111;color:#fff}}.wa{{background:#25D366;color:#fff}}</style></head>
    <body><div class="h"><a href="javascript:history.back()">← رجوع</a><b>شامي</b></div><div class="c"><img src="{img}"><div class="body"><h1>{title}</h1><hr>{"".join([f'<p>{p}</p>' for p in txt.split(chr(10))])}</div><div class="acts"><a href="{url}" target="_blank" class="btn src">فتح المصدر ↗</a><a href="https://wa.me/?text={urllib.parse.quote(title+' '+url)}" class="btn wa">واتساب</a></div></div></body></html>"""

@app.route('/api/news')
def api_news(): return jsonify(get_news(request.args.get('cat','الكل')))
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
        return """<!doctype html><html dir=rtl><head><meta charset=utf-8><meta name=viewport content=width=device-width,initial-scale=1><style>body{font-family:Tahoma;background:#f0f2f5;display:flex;justify-content:center;align-items:center;height:100vh;margin:0}.box{background:#fff;padding:30px;border-radius:12px;width:320px;text-align:center}input{width:100%;padding:12px;margin:8px 0}button{width:100%;padding:12px;background:#1b5e20;color:#fff;border:0;border-radius:8px}</style></head><body><form class=box method=post><h2>🔐 شامي</h2><input type=password name=password placeholder=shami123 required><button>دخول</button></form></body></html>"""
    lst="".join([f'<div style="background:#fff;padding:8px;margin:6px 0;display:flex;justify-content:space-between"><span>{n["title"][:30]}</span><form method=post><input type=hidden name=delete_index value={i}><button style="background:red;color:#fff;border:0;padding:4px 8px">حذف</button></form></div>' for i,n in enumerate(CUSTOM_NEWS)])
    return f"""<!doctype html><html dir=rtl><head><meta charset=utf-8><meta name=viewport content=width=device-width,initial-scale=1><style>body{{font-family:Tahoma;background:#f0f2f5;margin:0}}.h{{background:#1b5e20;color:#fff;padding:14px;text-align:center}}.c{{max-width:600px;margin:auto;padding:12px}}input,select{{width:100%;padding:10px;margin:5px 0}}.btn{{width:100%;background:#1b5e20;color:#fff;padding:10px;border:0;border-radius:8px}}</style></head><body><div class=h><h2>شامي - صور ثابتة ✅</h2></div><div class=c><form method=post style=background:#fff;padding:12px><input name=title placeholder="عنوان *" required><input name=image placeholder="رابط صورة"><input name=link placeholder="رابط"><select name=category><option>الكل</option><option>رياضة ⚽</option><option>عاجل 🔴</option><option>سياسة 🏛️</option></select><button class=btn>نشر</button></form>{lst}</div></body></html>"""

@app.route('/')
def home():
    cat=request.args.get('cat','الكل')
    news=get_news(cat)
    tabs="".join([f'<a href="/?cat={urllib.parse.quote(k)}" class="tab {"active" if k==cat else ""}">{k}</a>' for k in FEEDS])
    cards=""
    for i,n in enumerate(news):
        if i==4: cards+='<div class="card" style="background:#fff9c4;padding:12px;text-align:center;border:2px dashed #fbc02d">إعلانك هنا</div>'
        read_url=f"/read?url={urllib.parse.quote(n['link'])}&title={urllib.parse.quote(n['title'])}&img={urllib.parse.quote(n['image'])}"
        cards+=f'<div class="card"><img src="{n["image"]}" loading="lazy" onerror="this.src=\'{DEFAULT_IMAGES.get(cat)}\'"><div class="body"><span>{n["source"]} | {n["time"]}</span><h2>{n["title"]}</h2><div class="btns"><a href="{read_url}" class="r">📖 اقرأ</a><a href="{n["wa"]}" target="_blank" class="w">واتساب</a></div></div></div>'
    return f"""<!doctype html><html dir="rtl"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>شامي</title><link rel="manifest" href="/manifest.json"><style>body{{margin:0;font-family:Tahoma;background:#f0f2f5}}.h{{background:#1b5e20;color:#fff;padding:12px;display:flex;justify-content:space-between;position:sticky;top:0;z-index:10}}.tabs{{display:flex;gap:8px;overflow:auto;padding:10px;background:#fff;position:sticky;top:56px}}.tab{{padding:8px 14px;background:#eee;border-radius:20px;text-decoration:none;color:#333;white-space:nowrap;font-size:13px}}.tab.active{{background:#2e7d32;color:#fff}}.c{{max-width:700px;margin:auto;padding:10px}}.card{{background:#fff;border-radius:12px;overflow:hidden;margin:12px 0;box-shadow:0 2px 8px rgba(0,0,0,.08)}}.card img{{width:100%;height:200px;object-fit:cover}}.body{{padding:12px}}.body span{{font-size:12px;color:#666}}.body h2{{font-size:16px;margin:8px 0;line-height:1.4}}.btns{{display:flex;gap:8px;margin-top:10px}}.r,.w{{flex:1;text-align:center;padding:10px;border-radius:8px;color:#fff;font-weight:bold;text-decoration:none;font-size:14px}}.r{{background:#111}}.w{{background:#25D366}}</style></head>
    <body><div class="h"><div><h1 style="margin:0;font-size:17px">🔥 شامي - صور منظمة ✅</h1><div style="font-size:11px">رياضة 6 مصادر + صور حقيقية</div></div><a href="/admin" style="color:#fff;text-decoration:none">⚙️</a></div><div class="tabs">{tabs}</div><div class="c">{cards}</div></body></html>"""

if __name__=='__main__':
    port = int(os.environ.get("PORT", 10000))
    app.run(host='0.0.0.0', port=port)
