from flask import Flask, request, jsonify, redirect, Response
import feedparser, urllib.parse, re, os, json, time, concurrent.futures, requests
from datetime import datetime
app = Flask(__name__)
DATA_FILE="shami_data.json"
HEADERS={'User-Agent':'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'}

def load_data():
    try:
        with open(DATA_FILE,"r") as f: return json.load(f)
    except: return {"syp_black":15250}
def save_data(d):
    with open(DATA_FILE,"w") as f: json.dump(d,f)

# كل مصادرك + مصادر جديدة مجربة على Render
SPORTS=[
    {"url":"https://www.bbc.com/arabic/sport/rss.xml","name":"BBC رياضة ⚽"},
    {"url":"https://www.france24.com/ar/tag/رياضة/rss","name":"France24 رياضة 🇫🇷"},
    {"url":"https://www.aljazeera.net/xml/rss/all.xml","name":"الجزيرة رياضة 🌍"},
    {"url":"https://www.yallakora.com/rss/rss.aspx","name":"يلا كورة ⚽"},
    {"url":"https://www.beinsports.com/ar/rss","name":"beIN 🌍"},
]
POLITICS=[
    {"url":"https://www.bbc.com/arabic/index.xml","name":"BBC عربي 🌍"},
    {"url":"https://www.aljazeera.net/xml/rss/all.xml","name":"الجزيرة 🌍"},
    {"url":"https://sana.sy/feed/","name":"سانا 🇸🇾"},
    {"url":"https://www.france24.com/ar/rss","name":"France24 🌍"},
    {"url":"https://arabic.rt.com/rss/","name":"RT عربي 🇷🇺"},
]
ECONOMY=[
    {"url":"https://www.cnbcarabia.com/feed/","name":"CNBC عربية 💰"},
    {"url":"https://www.aljazeera.net/xml/rss/all.xml","name":"الجزيرة اقتصاد 💰"},
    {"url":"https://www.alarabiya.net/.mrss/ar/business.xml","name":"العربية Business"},
]
ART=[
    {"url":"https://www.bbc.com/arabic/art-and-culture/rss.xml","name":"BBC فن 🎭"},
    {"url":"https://www.france24.com/ar/tag/ثقافة/rss","name":"France24 ثقافة 🎭"},
    {"url":"https://www.skynewsarabia.com/web/rss","name":"سكاي نيوز منوعات"},
]
GENERAL=[
    {"url":"https://news.google.com/rss/search?q=سوريا&hl=ar&gl=SA&ceid=SA:ar","name":"سوريا 🇸🇾"},
    {"url":"https://www.bbc.com/arabic/index.xml","name":"BBC 🌍"},
]

DEFAULT_IMG="https://images.unsplash.com/photo-1495020689067-958852a7765e?w=600"
CACHE={}; CACHE_TIME={}; PCACHE={"data":None,"time":0}

def get_prices():
    now=time.time()
    if PCACHE["data"] and now-PCACHE["time"]<30: return PCACHE["data"]
    try:
        syp=load_data().get("syp_black",15250)
        r=requests.get("https://api.coingecko.com/api/v3/simple/price?ids=bitcoin,ethereum&vs_currencies=usd",headers=HEADERS,timeout=4).json()
        data={"btc":f"${r.get('bitcoin',{}).get('usd',84165):,.0f}","eth":f"${r.get('ethereum',{}).get('usd',2688):,.0f}","gold":"$4,286","syp_black":f"{syp:,}","updated":datetime.now().strftime("%H:%M")}
        PCACHE["data"]=data; PCACHE["time"]=now; return data
    except:
        syp=load_data().get("syp_black",15250)
        return {"btc":"$84,165","eth":"$2,688","gold":"$4,286","syp_black":f"{syp:,}","updated":datetime.now().strftime("%H:%M")}

def get_img(e):
    try:
        if hasattr(e,'media_content') and e.media_content:
            u=e.media_content[0].get('url','')
            if u.startswith('http'): return u
    except: pass
    m=re.search(r'<img[^>]+src="([^"]+)"', getattr(e,'description',''))
    return m.group(1) if m else DEFAULT_IMG

def fetch_one(src):
    try:
        resp=requests.get(src["url"], headers=HEADERS, timeout=7)
        if resp.status_code!=200: return []
        f=feedparser.parse(resp.content)
        res=[]
        for en in f.entries[:8]:
            res.append({"title":en.title,"link":en.link,"time":getattr(en,'published','')[:16],"source":src["name"],"image":get_img(en)})
        return res
    except: return []

def get_news(cat):
    now=time.time()
    if cat in CACHE and now-CACHE_TIME.get(cat,0)<300: return CACHE[cat]
    all_news=[]
    srcs=[]
    if cat=="رياضة ⚽": srcs=SPORTS
    elif cat=="سياسة 🏛️": srcs=POLITICS
    elif cat=="اقتصاد 💰": srcs=ECONOMY
    elif cat=="فن 🎭": srcs=ART
    elif cat=="أسعار 💱": srcs=[]
    else: srcs=GENERAL

    if srcs:
        with concurrent.futures.ThreadPoolExecutor(max_workers=5) as ex:
            for r in ex.map(fetch_one, srcs): all_news.extend(r)

    if not all_news and cat in CACHE: return CACHE[cat]
    if not all_news:
        all_news=[{"title":f"جاري تحديث {cat} - حدث الصفحة","link":"/","time":datetime.now().strftime("%H:%M"),"source":"شامي","image":DEFAULT_IMG}]

    CACHE[cat]=all_news[:30]; CACHE_TIME[cat]=now
    return CACHE[cat]

@app.route('/')
def home():
    cat=request.args.get('cat','الكل')
    prices=get_prices()
    tabs=[ "الكل","عاجل 🔴","رياضة ⚽","سياسة 🏛️","اقتصاد 💰","فن 🎭","أسعار 💱" ]
    tabs_html="".join([f'<a href="/?cat={urllib.parse.quote(k)}" class="tab {"active" if k==cat else ""}">{k}</a>' for k in tabs])

    if cat=="أسعار 💱":
        return f'<html dir="rtl"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><style>body{{font-family:system-ui;background:#f2f3f5;margin:0}}.top{{background:#1b5e20;color:#fff;padding:12px}}.tabs{{display:flex;gap:8px;overflow:auto;padding:10px;background:#fff}}.tab{{padding:10px 16px;background:#eceff1;border-radius:20px;text-decoration:none;color:#333}}.tab.active{{background:#1b5e20;color:#fff}}.box{{padding:20px;background:#fff;margin:20px;border-radius:12px}} </style></head><body><div class="top"><b>💱 أسعار شامي {prices["updated"]}</b> <a href="/" style="color:#fff;float:left">رجوع</a></div><div class="tabs">{tabs_html}</div><div class="box"><h3>💵 دمشق: {prices["syp_black"]} ل.س</h3><h3>₿ BTC: {prices["btc"]}</h3><h3>ETH: {prices["eth"]}</h3><h3>🪙 ذهب: {prices["gold"]}</h3><p>عدل السعر من /admin</p></div></body></html>'

    news=get_news(cat)
    cards="".join([f'<div class="card"><div class="imgw"><img src="{n["image"]}" loading="lazy" onerror="this.src=\'{DEFAULT_IMG}\'"><span class="badge">{n["source"]}</span></div><div class="info"><small>{n["time"]}</small><h2>{n["title"]}</h2><div class="btns"><a href="{n["link"]}" target="_blank" class="btn-r">📖 اقرأ</a><a href="https://wa.me/?text={urllib.parse.quote(n["title"]+" "+n["link"])}" target="_blank" class="btn-w">واتساب</a></div></div></div>' for n in news])

    return f'''<!doctype html>
