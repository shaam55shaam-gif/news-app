from flask import Flask, request, jsonify, redirect, Response
import feedparser, urllib.parse, re, os, json, time, concurrent.futures, requests
from datetime import datetime
app = Flask(__name__)
DATA_FILE="shami_data.json"

def load_data():
    try:
        with open(DATA_FILE,"r") as f: return json.load(f)
    except: return {"syp_black":15250}
def save_data(d):
    with open(DATA_FILE,"w") as f: json.dump(d,f)

SPORTS=[
    {"url":"https://www.yallakora.com/rss/rss.aspx","name":"يلا كورة ⚽"},
    {"url":"https://www.beinsports.com/ar/rss","name":"beIN 🌍"},
]
POLITICS=[
    {"url":"https://www.bbc.com/arabic/index.xml","name":"BBC 🌍"},
    {"url":"https://www.aljazeera.net/xml/rss/all.xml","name":"الجزيرة 🌍"},
    {"url":"https://sana.sy/feed/","name":"سانا 🇸🇾"},
]

DEFAULT_IMG="https://images.unsplash.com/photo-1495020689067-958852a7765e?w=600"
CACHE={}; CACHE_TIME={}; PCACHE={"data":None,"time":0}; DCACHE={"data":None,"time":0}

def get_real_prices():
    now=time.time()
    if PCACHE["data"] and now-PCACHE["time"]<30: return PCACHE["data"]
    try:
        syp=load_data().get("syp_black",15250)
        r=requests.get("https://api.coingecko.com/api/v3/simple/price?ids=bitcoin,ethereum&vs_currencies=usd",timeout=4).json()
        data={"btc":f"${r.get('bitcoin',{}).get('usd',84163):,.0f}","eth":f"${r.get('ethereum',{}).get('usd',2688):,.0f}","gold":"$4,286","syp_black":f"{syp:,}","updated":datetime.now().strftime("%H:%M")}
        PCACHE["data"]=data; PCACHE["time"]=now; return data
    except:
        syp=load_data().get("syp_black",15250)
        return {"btc":"$84,163","eth":"$2,688","gold":"$4,286","syp_black":f"{syp:,}","updated":datetime.now().strftime("%H:%M")}

def get_detailed():
    now=time.time()
    if DCACHE["data"] and now-DCACHE["time"]<90: return DCACHE["data"]
    try:
        syp_rate=load_data().get("syp_black",15250)
        fx=requests.get("https://api.exchangerate-api.com/v4/latest/USD",timeout=5).json()
        rates=fx.get("rates",{}); TRY=rates.get("TRY",34.5)
        cr=requests.get("https://api.coingecko.com/api/v3/simple/price?ids=bitcoin,ethereum,solana&vs_currencies=usd&include_24hr_change=true",timeout=5).json()
        currencies=[
            {"name":"السورية السوداء 🇸🇾","from":f"1$ = {syp_rate:,} ل.س","to":f"1 ل.س = {1/syp_rate:.7f} $","hl":True},
            {"name":"التركية 🇹🇷","from":f"1$ = {TRY:.2f} TL","to":f"1 TL = {syp_rate/TRY:,.0f} ل.س"},
            {"name":"السعودي 🇸🇦","from":f"1$ = {rates.get('SAR',3.75):.2f} ر.س","to":f"1 ر.س = {syp_rate/rates.get('SAR',3.75):,.0f} ل.س"},
            {"name":"اليورو 🇪🇺","from":f"1$ = {rates.get('EUR',0.92):.3f} €","to":f"1 € = {syp_rate/rates.get('EUR',0.92):,.0f} ل.س"},
        ]
        data={"currencies":currencies,"gold":{"oz":4286,"g_syp":int(4286/31.1035*syp_rate)},"crypto":[{"n":"BTC","p":cr.get("bitcoin",{}).get("usd",84163),"c":cr.get("bitcoin",{}).get("usd_24h_change",0)},{"n":"ETH","p":cr.get("ethereum",{}).get("usd",2688),"c":cr.get("ethereum",{}).get("usd_24h_change",0)}],"updated":datetime.now().strftime("%H:%M:%S")}
        DCACHE["data"]=data; DCACHE["time"]=now; return data
    except:
        syp=load_data().get("syp_black",15250)
        return {"currencies":[{"name":"السورية 🇸🇾","from":f"1$ = {syp:,} ل.س","to":f"1 ل.س"}],"gold":{"oz":4286,"g_syp":2090000},"crypto":[{"n":"BTC","p":84163,"c":0}],"updated":datetime.now().strftime("%H:%M:%S")}

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
        f=feedparser.parse(src["url"])
        res=[]
        for en in f.entries[:8]:
            res.append({"title":en.title,"link":en.link,"time":getattr(en,'published','')[:16],"source":src["name"],"image":get_img(en)})
        return res
    except: return []

def get_news(cat):
    now=time.time()
    if cat in CACHE and now-CACHE_TIME.get(cat,0)<300: return CACHE[cat]
    all_news=[]
    if cat=="رياضة ⚽":
        with concurrent.futures.ThreadPoolExecutor(max_workers=2) as ex:
            for r in ex.map(fetch_one, SPORTS): all_news.extend(r)
    elif cat=="سياسة 🏛️":
        with concurrent.futures.ThreadPoolExecutor(max_workers=2) as ex:
            for r in ex.map(fetch_one, POLITICS): all_news.extend(r)
    elif cat=="أسعار 💱":
        all_news=[]
    else: # الكل وعاجل
        try:
            url = "https://news.google.com/rss/search?q=سوريا&hl=ar&gl=SA&ceid
