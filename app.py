from flask import Flask, request, Response, redirect, session
import feedparser, urllib.parse, json, re, os, time, concurrent.futures, requests
from datetime import datetime

app = Flask(__name__)
app.secret_key = "shami_images_fixed"

FEEDS = {
    "الكل": "https://news.google.com/rss/search?q=سوريا&hl=ar&gl=SA&ceid=SA:ar",
    "عاجل 🔴": "https://news.google.com/rss/search?q=عاجل+سوريا&hl=ar&gl=SA&ceid=SA:ar",
    "رياضة ⚽": "https://www.yallakora.com/rss/rss.aspx",
    "اقتصاد 💰": "https://news.google.com/rss/search?q=اقتصاد+سوريا&hl=ar&gl=SA&ceid=SA:ar",
    "سياسة 🏛️": "https://www.bbc.com/arabic/index.xml",
    "ثقافية 🎭": "https://sana.sy/feed/",
    "فن 🎨": "https://www.snacksyrian.com/feed/"
}

SPORTS_SOURCES = [
    {"url": "https://www.yallakora.com/rss/rss.aspx", "name": "يلا كورة ⚽"},
    {"url": "https://www.beinsports.com/ar/rss", "name": "beIN 🌍"},
    {"url": "https://sana.sy/feed/", "name": "سانا رياضة 🇸🇾"},
    {"url": "https://www.kooora.com/rss.aspx", "name": "كووورة ⚽"},
    {"url": "https://www.goal.com/ar/rss", "name": "Goal ⚽"},
]

POLITICS_SOURCES = [
    {"url": "https://www.bbc.com/arabic/index.xml", "name": "BBC 🌍"},
    {"url": "https://www.aljazeera.net/xml/rss/all.xml", "name": "الجزيرة 🌍"},
    {"url": "https://sana.sy/feed/", "name": "سانا سياسة 🇸🇾"},
    {"url": "https://www.skynewsarabia.com/web/rss", "name": "سكاي نيوز 🌍"},
    {"url": "https://arabic.cnn.com/rss", "name": "CNN 🌍"},
]

ECONOMY_SOURCES = [
    {"url": "https://www.aljazeera.net/xml/rss/all.xml", "name": "الجزيرة 💰"},
    {"url": "https://sana.sy/feed/", "name": "سانا اقتصاد 🇸🇾"},
]

EXTRA_FEEDS = {
    "الكل": POLITICS_SOURCES[:3] + SPORTS_SOURCES[:2],
    "عاجل 🔴": POLITICS_SOURCES[:4],
    "رياضة ⚽": SPORTS_SOURCES,
    "سياسة 🏛️": POLITICS_SOURCES,
    "اقتصاد 💰": ECONOMY_SOURCES,
    "ثقافية 🎭": [{"url": "https://sana.sy/feed/", "name": "سانا"}],
    "فن 🎨": [{"url": "https://www.snacksyrian.com/feed/", "name": "سناك"}]
}

DEFAULT_IMAGES = {
    "الكل": "https://images.unsplash.com/photo-1495020689067-958852a7765e?w=600",
    "عاجل 🔴": "https://images.unsplash.com/photo-1586339949916-3e9457bef6d3?w=600",
    "رياضة ⚽": "https://images.unsplash.com/photo-1461896836934-ffe607ba8211?w=600",
    "اقتصاد 💰": "https://images.unsplash.com/photo-1611974789855-9c2a0a7236a3?w=600",
    "سياسة 🏛️": "https://images.unsplash.com/photo-1529107386315-e1a2ed48a620?w=600",
}

def get_image_from_entry(entry, cat):
    # 1- من الـ RSS نفسه
    try:
        if hasattr(entry, 'media_content') and entry.media_content:
            u = entry.media_content[0].get('url','')
            if u.startswith('http') and 'logo' not in u.lower(): return u
        if hasattr(entry, 'media_thumbnail') and entry.media_thumbnail:
            u = entry.media_thumbnail[0].get('url','')
            if u.startswith('http'): return u
    except: pass
    desc = getattr(entry, 'description','') + getattr(entry, 'summary','')
    m = re.search(r'<img[^>]+src="([^"]+)"', desc)
    if m and m.group(1).startswith('http') and 'logo' not in m.group(1).lower():
        return m.group(1)
    return None

def get_og_image(url):
    # بيجيب الصورة الحقيقية من صفحة الخبر
    try:
        r = requests.get(url, headers={'User-Agent':'Mozilla/5.0'}, timeout=3)
        m = re.search(r'<meta[^>]+property="og:image"[^>]+content="([^"]+)"', r.text, re.I)
        if m: return m.group(1)
        m2 = re.search(r'<meta[^>]+content="([^"]+)"[^>]+property="og:image"', r.text, re.I)
        if m2: return m2.group(1)
        m3 = re.search(r'<img[^>]+src="([^"]+\.(jpg|jpeg|png|webp)[^"]*)"', r.text, re.I)
        if m3: return m3.group(1)
    except: pass
    return None

CACHE = {}
CACHE_TIME = {}

def fetch_one(args):
    src, cat = args
    try:
        f = feedparser.parse(src["url"])
        res=[]
        for e in f.entries[:4]:
            img = get_image_from_entry(e, cat)
            if not img: # اذا ما في صورة بالـ RSS جيبها من الرابط
                img = get_og_image(e.link) or DEFAULT_IMAGES.get(cat)
            res.append({"title":e.title,"link":e.link,"time":getattr(e,'published','')[:16] or datetime.now().strftime("%H:%M"),"source":src["name"],"image":img,"wa":f"https://wa.me/?text={urllib.parse.quote(e.title)}"})
        return res
    except:
        return []

def get_news(cat, query=None):
    now=time.time()
    key=f"{cat}_{query or ''}"
    if key in CACHE and now-CACHE_TIME.get(key,0)<300:
        return CACHE[key]

    if query:
        try:
            feed=feedparser.parse(f"https://news.google.com/rss/search?q={urllib.parse.quote(query)}&hl=ar&gl=SA&ceid=SA:ar")
            res=[]
            for e in feed.entries[:10]:
                img = get_image_from_entry(e, cat) or get_og_image(e.link) or DEFAULT_IMAGES.get(cat)
                res.append({"title":e.title,"link":e.link,"time":getattr(e,'published','')[:16],"source":"بحث 🔍","image":img,"wa":f"https://wa.me/?text={urllib.parse.quote(e.title)}"})
            CACHE[key]=res
            CACHE_TIME[key]=now
            return res
        except:
            return []

    all_news=[]
    sources = EXTRA_FEEDS.get(cat, [])[:6]
    if sources:
        with concurrent.futures.ThreadPoolExecutor(max_workers=6) as ex:
            results = list(ex.map(fetch_one, [(s, cat) for s in sources]))
            for r in results:
                all_news.extend(r)

    # Google آخر شي وبس خبرين
    try:
        fg=feedparser.parse(FEEDS.get(cat))
        for e in fg.entries[:2]:
            img = get_image_from_entry(e, cat) or get_og_image(e.link) or DEFAULT_IMAGES.get(cat)
            all_news.append({"title":e.title,"link":e.link,"time":getattr(e,'published','')[:16],"source":"Google","image":img,"wa":f"https://wa.me/?text={urllib.parse.quote(e.title)}"})
    except: pass

    CACHE[key]=all_news[:25]
    CACHE_TIME[key]=now
    return all_news[:25] if all_news else [{"title":f"لا يوجد أخبار في {cat}","link":"#","time":datetime.now().strftime("%H:%M"),"source":"شامي","image":DEFAULT_IMAGES.get(cat),"wa":"#"}]

@app.route('/search')
def search():
    q=request.args.get('q','').strip()
    if not q: return redirect('/')
    return home_render("الكل", get_news("الكل", query=q), q)

def home_render(cat, news, q=None):
    tabs="".join([f'<a href="/?cat={urllib.parse.quote(k)}" class="tab {"active" if k==cat and not q else ""}">{k}</a>' for k in FEEDS])
    economy_bar='<div style="background:#0d2818;color:#fff;padding:10px 14px;display:flex;justify-content:space-between;font-size:13px;border-radius:10px;margin:10px"><span>💵 دمشق: ~15,200</span><span>🪙 ذهب: 1.1M</span><span style="background:#25D366;padding:2px 8px;border-radius:10px">مباشر</span></div>'
    search_box=f'''
    <div style="background:#fff;padding:10px;position:sticky;top:56px;z-index:9;border-bottom:1px solid #eee">
      <form action="/search" method="get" style="display:flex;gap:8px;max-width:700px;margin:auto">
        <input name="q" value="{q or ''}" placeholder="🔍 ابحث: برشلونة، الدولار، سياسة..." style="flex:1;padding:10px 14px;border:1px solid #ddd;border-radius:20px;font-family:Tahoma">
        <button style="background:#1b5e20;color:#fff;border:0;padding:10px 18px;border-radius:20px;font-weight:bold">بحث</button>
      </form>
    </div>'''
    title_bar=f'<div style="padding:10px;background:#e8f5e9;text-align:center">نتائج "{q}" - {len(news)} خبر <a href="/">✕</a></div>' if q else ""
    cards=""
    for i,n in enumerate(news):
        if not q and i==2: cards+=economy_bar
        wa=n["wa"]
        cards+=f'<div class="card"><img src="{n["image"]}" loading="lazy" referrerpolicy="no-referrer"><div class="body"><span>{n["source"]} | {n["time"]}</span><h2>{n["title"]}</h2><div class="btns"><a href="{n["link"]}" target="_blank" class="r">📖 اقرأ</a><a href="{wa}" target="_blank" class="w">واتساب</a></div></div></div>'
    return f"""<!doctype html><html dir="rtl"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>شامي</title>
    <style>body{{margin:0;font-family:Tahoma;background:#f0f2f5}}.h{{background:#1b5e20;color:#fff;padding:12px;display:flex;justify-content:space-between;position:sticky;top:0;z-index:10}}.tabs{{display:flex;gap:8px;overflow:auto;padding:10px;background:#fff;position:sticky;top:105px}}.tab{{padding:8px 14px;background:#eee;border-radius:20px;text-decoration:none;color:#333;white-space:nowrap;font-size:13px}}.tab.active{{background:#2e7d32;color:#fff}}.c{{max-width:700px;margin:auto;padding:10px}}.card{{background:#fff;border-radius:12px;overflow:hidden;margin:12px 0;box-shadow:0 2px 8px rgba(0,0,0,.08)}}.card img{{width:100%;height:210px;object-fit:cover;background:#eee}}.body{{padding:12px}}.body span{{font-size:11px;color:#666}}.body h2{{font-size:15px;margin:8px 0;line-height:1.5}}.btns{{display:flex;gap:8px}}.r,.w{{flex:1;text-align:center;padding:10px;border-radius:8px;color:#fff;font-weight:bold;text-decoration:none}}.r{{background:#111}}.w{{background:#25D366}}</style></head>
    <body><div class="h"><div><h1 style="margin:0;font-size:16px">🔥 شامي - صور حقيقية ✅</h1><div style="font-size:11px">6 رياضة + 5 سياسة + بحث + صور من المصدر</div></div></div>{search_box}<div class="tabs">{tabs}</div>{title_bar}<div class="c">{cards}</div></body></html>"""

@app.route('/')
def home():
    return home_render(request.args.get('cat','الكل'), get_news(request.args.get('cat','الكل')))

if __name__=='__main__':
    port=int(os.environ.get("PORT",10000))
    app.run(host='0.0.0.0',port=port)
