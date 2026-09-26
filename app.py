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
        clean=[re.sub(r'<[^>]+>', '', p).strip() for p in ps[:12] if len(re.sub(r'<[^
