from flask import Flask, request, Response, redirect, session, jsonify
import feedparser, urllib.parse, json, re, os, requests, threading, time
from datetime import datetime

app = Flask(__name__)
app.secret_key = "shami_final_fast"

FEEDS = {
    "الكل": "https://news.google.com/rss/search?q=سوريا&hl=ar&gl=SA&ceid=SA:ar",
    "عاجل 🔴": "https://news.google.com/rss/search?q=عاجل+سوريا&hl=ar&gl=SA&ceid=SA:ar",
    "رياضة ⚽": "https://news.google.com/rss/search?q=رياضة+سورية&hl=ar&gl=SA&ceid=SA:ar",
    "اقتصاد 💰": "https://news.google.com/rss/search?q=اقتصاد&hl=ar&gl=SA&ceid=SA:ar",
    "سياسة 🏛️": "https://news.google.com/rss/search?q=سياسة+سوريا&hl=ar&gl=SA&ceid=SA:ar",
    "ثقافية 🎭": "https://news.google.com/rss/search?q=ثقافة&hl=ar&gl=SA&ceid=SA:ar",
    "فن 🎨": "https://news.google.com/rss/search?q=فن+مشاهير&hl=ar&gl=SA&ceid=SA:ar"
}

SPORTS_SOURCES = [
    {"url": "https://sana.sy/feed/", "name": "سانا - رياضة 🇸🇾"},
    {"url": "https://www.kooora.com/rss/rss.html", "name": "كووورة ⚽"},
    {"url": "https://www.yallakora.com/rss/rss.aspx", "name": "يلا كورة ⚽"},
    {"url": "https://www.filgoal.com/rss", "name": "فيلجول 🏆"},
    {"url": "https://www.beinsports.com/ar/rss", "name": "beIN Sports 🌍"},
    {"url": "https://www.goal.com/ar/rss", "name": "Goal 🌍"},
    {"url": "https://news.google.com/rss/search?q=الدوري+الانجليزي+الاسباني+ابطال+اوروبا&hl=ar&gl=SA&ceid=SA:ar", "name": "بطولات عالمية 🏆"},
    {"url": "https://news.google.com/rss/search?q=الدوري+السعودي+المصري+السوري+ابطال+اسيا&hl=ar&gl=SA&ceid=SA:ar", "name": "بطولات عربية وسورية 🏆"},
]

EXTRA_FEEDS = {
    "الكل": ["https://sana.sy/feed/", "https://www.bbc.com/arabic/index.xml"],
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

def get_image(entry):
    if hasattr(entry, 'media_content'): return entry.media_content[0]['url']
    if hasattr(entry, 'media_thumbnail'): return entry.media_thumbnail[0]['url']
    m = re.search(r'<img[^>]+src="([^"]+)"', getattr(entry, 'description', ''))
    if m: return m.group(1)
    return "https://images.unsplash.com/photo-1513151233558-d860c5398176?w=600"

CACHE = {}

def fetch_one_cat(cat):
    try:
        all_news = []
        feed = feedparser.parse(FEEDS.get(cat))
        for e in feed.entries[:6]:
            all_news.append({"title":e.title,"link":e.link,"time":getattr(e,'published','')[:16] or datetime.now().strftime("%H:%M"),"source":"Google","image":get_image(e),"wa":f"https://wa.me/?text={urllib.parse.quote(e.title)}","is_custom":False})
        for src in EXTRA_FEEDS.get(cat, []):
            try:
                url = src["url"] if isinstance(src, dict) else src
                name = src["name"] if isinstance(src, dict) else "مصدر"
                f2 = feedparser.parse(url)
                for e in f2.entries[:3]:
                    all_news.append({"title":e.title,"link":e.link,"time":getattr(e,'published','')[:16],"source":name,"image":get_image(e),"wa":f"https://wa.me/?text={urllib.parse.quote(e.title)}","is_custom":False})
            except: continue
        CACHE[cat] = all_news[:30]
        print(f"تم تحديث {cat}")
    except: pass

def fetch_all_news():
    while True:
        for cat in FEEDS:
            fetch_one_cat(cat)
        time.sleep(180)

threading.Thread(target=fetch_all_news, daemon=True).start()

def get_news(cat):
    cf = [n for n in CUSTOM_NEWS if cat == "الكل" or n.get("category")==cat]
    if cat not in CACHE or not CACHE[cat]:
        fetch_one_cat(cat)
    cached = CACHE.get(cat, [])
    return cf + cached if (cf or cached) else [{"title":f"جاري تحديث {cat} - حدث الصفحة","link":"#","time":datetime.now().strftime("%H:%M"),"source":"شامي","image":"https://images.unsplash.com/photo-1513151233558-d860c5398176?w=600","wa":"#","is_custom":False}]

@app.route('/read')
def read_article():
    url = request.args.get('url',''); title = request.args.get('title','خبر'); img = request.args.get('img','')
    if not url or url == "#": return redirect('/')
    article_text=""
    try:
        r = requests.get(url, headers={'User-Agent':'Mozilla/5.0'}, timeout=6)
        paragraphs = re.findall(r'<p[^>]*>(.*?)</p>', r.text, re.DOTALL)
        clean=[re.sub(r'<[^>]+>', '', p).strip() for p in paragraphs[:20] if len(re.sub(r'<[^>]+>', '', p).strip())>50]
        article_text = "\n".join(clean) if clean else "افتح المصدر لقراءة كامل الخبر"
    except: article_text = "افتح المصدر"
    return f"""<!doctype html><html dir="rtl"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>{title[:50]}</title>
    <style>body{{margin:0;font-family:Tahoma;background:#f5f5f5}}.h{{background:#1b5e20;color:#fff;padding:12px;display:flex;gap:10px;position:sticky;top:0}}.h a{{color:#fff;text-decoration:none;background:rgba(255,255,255,.2);padding:6px 14px;border-radius:20px}}.c{{max-width:700px;margin:auto;background:#fff}}.c img{{width:100%;max-height:360px;object-fit:cover}}.body{{padding:18px}}.body h1{{font-size:21px}}p{{font-size:17px;line-height:1.9;margin:14px 0}}.acts{{display:flex;gap:10px;padding:16px;position:sticky;bottom:0;background:#fff}}.btn{{flex:1;padding:12px;text-align:center;border-radius:10px;text-decoration:none;font-weight:bold}}.src{{background:#111;color:#fff}}.wa{{background:#25D366;color:#fff}}</style></head>
    <body><div class="h"><a href="javascript:history.back()">← رجوع</a><b>شامي</b></div><div class="c"><img src="{img}"><div class="body"><h1>{title}</h1><hr>{"".join([f'<p>{p}</p>' for p in article_text.split(chr(10))])}</div><div class="acts"><a href="{url}" target="_blank" class="btn src">فتح المصدر ↗</a><a href="https://wa.me/?text={urllib.parse.quote(title+' '+url)}" target="_blank" class="btn wa">واتساب</a></div></div></body></html>"""

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
            CUSTOM_NEWS.insert(0, {"title":request.form.get('title'),"link":request.form.get('link') or "#","time":datetime.now().strftime("%H:%M"),"source":"خاص 🔥","image":request.form.get('image') or "https://images.unsplash.com/photo-1513151233558-d860c5398176?w=600","wa":f"https://wa.me/?text={urllib.parse.quote(request.form.get('title'))}","is_custom":True,"category":request.form.get('category','الكل')})
            save_custom()
        elif request.form.get('delete_index') is not None:
            try: CUSTOM_NEWS.pop(int(request.form.get('delete_index'))); save
