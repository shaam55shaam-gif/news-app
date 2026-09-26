from flask import Flask, request, Response, jsonify
import feedparser, urllib.parse, json, re, os, time, concurrent.futures, requests
from datetime import datetime

app = Flask(__name__)

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
    {"url": "https://sana.sy/feed/", "name": "سانا 🇸🇾"},
    {"url": "https://www.kooora.com/rss.aspx", "name": "كووورة ⚽"},
    {"url": "https://www.goal.com/ar/rss", "name": "Goal"},
]
POLITICS_SOURCES = [
    {"url": "https://www.bbc.com/arabic/index.xml", "name": "BBC"},
    {"url": "https://www.aljazeera.net/xml/rss/all.xml", "name": "الجزيرة"},
    {"url": "https://sana.sy/feed/", "name": "سانا"},
    {"url": "https://www.skynewsarabia.com/web/rss", "name": "سكاي نيوز"},
]
EXTRA_FEEDS = {
    "الكل": POLITICS_SOURCES[:3] + SPORTS_SOURCES[:2],
    "عاجل 🔴": POLITICS_SOURCES[:4],
    "رياضة ⚽": SPORTS_SOURCES,
    "سياسة 🏛️": POLITICS_SOURCES,
    "اقتصاد 💰": [{"url": "https://www.aljazeera.net/xml/rss/all.xml", "name": "اقتصاد"}],
    "ثقافية 🎭": [{"url": "https://sana.sy/feed/", "name": "سانا"}],
    "فن 🎨": [{"url": "https://www.snacksyrian.com/feed/", "name": "سناك"}]
}
DEFAULT_IMAGES = {
    "الكل": "https://images.unsplash.com/photo-1495020689067-958852a7765e?w=600",
    "رياضة ⚽": "https://images.unsplash.com/photo-1461896836934-ffe607ba8211?w=600",
}

PRICES_CACHE = {"data": None, "time": 0}
TRANSLATE_CACHE = {}

def get_real_prices():
    now = time.time()
    if PRICES_CACHE["data"] and now - PRICES_CACHE["time"] < 60:
        return PRICES_CACHE["data"]
    try:
        crypto = requests.get("https://api.coingecko.com/api/v3/simple/price?ids=bitcoin,ethereum&vs_currencies=usd&include_24hr_change=true", timeout=4).json()
        gold_resp = requests.get("https://api.gold-api.com/price/XAU", timeout=4).json()
        gold_price = gold_resp.get("price", 2650) if isinstance(gold_resp, dict) else 2650
        data = {
            "btc": f"${crypto.get('bitcoin',{}).get('usd',67200):,.0f}",
            "btc_change": f"{crypto.get('bitcoin',{}).get('usd_24h_change',1.2):.1f}%",
            "eth": f"${crypto.get('ethereum',{}).get('usd',3800):,.0f}",
            "gold": f"${gold_price:,.0f}",
            "syp": "15,250",
            "updated": datetime.now().strftime("%H:%M:%S")
        }
        PRICES_CACHE["data"]=data; PRICES_CACHE["time"]=now
        return data
    except:
        return PRICES_CACHE["data"] or {"btc":"$67,200","btc_change":"+1.2%","eth":"$3,800","gold":"$2,650","syp":"15,250","updated":datetime.now().strftime("%H:%M")}

def translate_to_ar(text):
    if re.search(r'[\u0600-\u06FF]', text): return text
    if text in TRANSLATE_CACHE: return TRANSLATE_CACHE[text]
    try:
        url = f"https://translate.googleapis.com/translate_a/single?client=gtx&sl=auto&tl=ar&dt=t&q={urllib.parse.quote(text)}"
        r = requests.get(url, timeout=3).json()
        trans = "".join([s[0] for s in r[0]])
        TRANSLATE_CACHE[text]=trans
        return trans
    except: return text

def get_image(entry, cat):
    try:
        if hasattr(entry,'media_content') and entry.media_content:
            u=entry.media_content[0].get('url','')
            if u.startswith('http') and 'logo' not in u.lower(): return u
    except: pass
    m=re.search(r'<img[^>]+src="([^"]+)"', getattr(entry,'description',''))
    if m and m.group(1).startswith('http'): return m.group(1)
    return None
def get_og(url):
    try:
        r=requests.get(url, headers={'User-Agent':'Mozilla/5.0'}, timeout=3)
        m=re.search(r'property="og:image"[^>]+content="([^"]+)"', r.text, re.I)
        if m: return m.group(1)
    except: pass
    return None

CACHE={}; CACHE_TIME={}
def fetch_one(args):
    src, cat=args
    try:
        f=feedparser.parse(src["url"])
        res=[]
        for e in f.entries[:3]:
            img=get_image(e,cat) or get_og(e.link) or DEFAULT_IMAGES.get(cat, DEFAULT_IMAGES["الكل"])
            title=translate_to_ar(e.title)
            res.append({"title":title,"link":e.link,"time":getattr(e,'published','')[:16],"source":src["name"],"image":img,"wa":f"https://wa.me/?text={urllib.parse.quote(title)}"})
        return res
    except: return []

def get_news(cat, q=None):
    now=time.time(); key=f"{cat}_{q or ''}"
    if key in CACHE and now-CACHE_TIME.get(key,0)<180: return CACHE[key]
    if q:
        try:
            feed=feedparser.parse(f"https://news.google.com/rss/search?q={urllib.parse.quote(q)}&hl=ar&gl=SA&ceid=SA:ar")
            res=[]
            for e in feed.entries[:15]:
                img=get_image(e,cat) or get_og(e.link) or DEFAULT_IMAGES["الكل"]
                res.append({"title":translate_to_ar(e.title),"link":e.link,"time":getattr(e,'published','')[:16],"source":"بحث 🔍","image":img,"wa":f"https://wa.me/?text={urllib.parse.quote(e.title)}"})
            CACHE[key]=res; CACHE_TIME[key]=now; return res
        except: return []
    all_news=[]
    sources=EXTRA_FEEDS.get(cat,[])[:5]
    if sources:
        with concurrent.futures.ThreadPoolExecutor(max_workers=5) as ex:
            results=list(ex.map(fetch_one, [(s,cat) for s in sources]))
            for r in results: all_news.extend(r)
    CACHE[key]=all_news[:25]; CACHE_TIME[key]=now
    return all_news[:25]

@app.route('/api/prices')
def api_prices(): return jsonify(get_real_prices())

def home_render(cat, news, q=None):
    prices=get_real_prices()
    urgent=get_news("عاجل 🔴")[:5]
    ticker_text=" • ".join([n["title"] for n in urgent])
    tabs_html="".join([f'<a href="/?cat={urllib.parse.quote(k)}" class="tab {"active" if k==cat and not q else ""}">{k}</a>' for k in FEEDS])

    cards_html=""
    for n in news:
        cards_html+=f'''
        <article class="news-card">
          <div class="img-wrap"><img src="{n["image"]}" loading="lazy"><span class="badge">{n["source"]}</span></div>
          <div class="info"><span class="meta">{n["time"]}</span><h2>{n["title"]}</h2>
          <div class="actions"><a href="{n["link"]}" target="_blank" class="btn-read">اقرأ 📖</a><a href="{n["wa"]}" target="_blank" class="btn-wa">واتساب</a></div></div>
        </article>'''

    return f"""<!doctype html><html dir="rtl" lang="ar"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
    <title>شامي - فرونت جديد</title>
    <link href="https://fonts.googleapis.com/css2?family=Tajawal:wght@400;700;800&display=swap" rel="stylesheet">
    <style>
      *{{font-family:'Tajawal',Tahoma, sans-serif;box-sizing:border-box}}body{{margin:0;background:#f6f7f9;color:#111}}
     .top-header{{background:linear-gradient(90deg,#0f4d23,#1b5e20);color:#fff;padding:14px 16px;position:sticky;top:0;z-index:20;display:flex;justify-content:space-between;align-items:center;box-shadow:0 2px 10px rgba(0,0,0,.2)}}
     .top-header h1{{margin:0;font-size:18px;font-weight:800}}.top-header small{{opacity:.8;font-size:11px}}
     .ticker{{background:#c62828;color:#fff;display:flex;align-items:center;overflow:hidden;height:40px}}
     .ticker-label{{background:#fff;color:#c62828;font-weight:800;padding:6px 14px;margin:0 10px;border-radius:6px;white-space:nowrap}}
     .ticker marquee{{font-weight:700;font-size:14px}}
     .prices{{background:#111;color:#eee;display:flex;gap:18px;overflow:auto;padding:10px 14px;font-size:13px;white-space:nowrap;scrollbar-width:none}}
     .prices b{{color:#25D366}}.prices::-webkit-scrollbar{{display:none}}
     .search-wrap{{background:#fff;padding:12px;position:sticky;top:60px;z-index:15;box-shadow:0 1px 4px rgba(0,0,0,.06)}}
     .search-wrap form{{max-width:700px;margin:auto;display:flex;gap:8px}}.search-wrap input{{flex:1;padding:12px 16px;border:1px solid #ddd;border-radius:24px;outline:none}}.search-wrap button{{background:#1b5e20;color:#fff;border:0;padding:12px 22px;border-radius:24px;font-weight:700}}
     .tabs{{display:flex;gap:10px;overflow:auto;padding:12px 16px;background:#fff;position:sticky;top:118px;z-index:14}}.tab{{padding:10px 18px;background:#eef0f2;border-radius:24px;text-decoration:none;color:#333;font-weight:700;font-size:13px;white-space:nowrap;transition:.2s}}.tab.active{{background:#1b5e20;color:#fff;box-shadow:0 3px 10px rgba(27,94,32,.3)}}
     .container{{max-width:750px;margin:auto;padding:12px}}
     .news-card{{background:#fff;border-radius:16px;overflow:hidden;margin:14px 0;box-shadow:0 4px 18px rgba(0,0,0,.06);transition:.2s}}.news-card:hover{{transform:translateY(-3px);box-shadow:0 8px 24px rgba(0,0,0,.12)}}
     .img-wrap{{position:relative}}.img-wrap img{{width:100%;height:220px;object-fit:cover;display:block}}.badge{{position:absolute;top:10px;right:10px;background:rgba(0,0,0,.7);color:#fff;padding:4px 10px;border-radius:20px;font-size:11px}}
     .info{{padding:14px}}.meta{{font-size:11px;color:#888}}.info h2{{margin:8px 0 12px;font-size:16px;line-height:1.5;font-weight:700}}
     .actions{{display:flex;gap:10px}}.btn-read,.btn-wa{{flex:1;text-align:center;padding:11px;border-radius:10px;text-decoration:none;font-weight:800;font-size:13px}}.btn-read{{background:#111;color:#fff}}.btn-wa{{background:#25D366;color:#fff}}
    </style>
    <script>setInterval(()=>{{fetch('/api/prices').then(r=>r.json()).then(d=>{{document.getElementById('prices').innerHTML=`<span>₿ ${{d.btc}} (${{d.btc_change}})</span><span>ETH ${{d.eth}}</span><span>🪙 ذهب ${{d.gold}}</span><span>💵 دمشق ${{d.syp}} ل.س</span><span>⏰ ${{d.updated}}</span>`;}});}},60000)</script>
    </head><body>
    <div class="top-header"><div><h1>🔥 شامي</h1><small>6 رياضة + 5 سياسة + أسعار حية + ترجمة</small></div><div style="font-size:22px">☰</div></div>
    <div class="ticker"><span class="ticker-label">عاجل 🔴</span><marquee scrollamount="6">{ticker_text}</marquee></div>
    <div class="prices" id="prices"><span>₿ {prices["btc"]} ({prices["btc_change"]})</span><span>ETH {prices["eth"]}</span><span>🪙 ذهب {prices["gold"]}</span><span>💵 دمشق {prices["syp"]} ل.س</span><span>⏰ {prices["updated"]}</span></div>
    <div class="search-wrap"><form action="/search"><input name="q" value="{q or ''}" placeholder="🔍 ابحث... برشلونة، الدولار، سياسة (ترجمة فورية)"><button>بحث</button></form></div>
    <div class="tabs">{tabs_html}</div>
    <div class="container">{cards_html}</div>
    </body></html>"""

@app.route('/search')
def search():
    q=request.args.get('q','').strip()
    if not q: return redirect('/')
    return home_render("الكل", get_news("الكل", q), q)

@app.route('/')
def home():
    cat=request.args.get('cat','الكل')
    return home_render(cat, get_news(cat))

if __name__=='__main__':
    port=int(os.environ.get("PORT",10000))
    app.run(host='0.0.0.0',port=port)
