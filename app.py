from flask import Flask, request, jsonify, redirect, Response
import feedparser, urllib.parse, re, os, json, time, concurrent.futures, requests
from datetime import datetime
app = Flask(__name__)
DATA_FILE = "shami_data.json"
HEADERS={'User-Agent':'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36','Accept':'application/rss+xml,application/xml;q=0.9,*/*;q=0.8'}

def load_data():
    try:
        with open(DATA_FILE,"r") as f: return json.load(f)
    except: return {"syp_black":15250}
def save_data(d):
    try:
        with open(DATA_FILE,"w") as f: json.dump(d,f)
    except: pass

# ===== مصادر مجربة وشغالة على Render 100% =====
SPORTS=[
    {"url":"https://www.yallakora.com/rss/rss.aspx","name":"يلا كورة ⚽"},
    {"url":"https://www.bbc.com/arabic/sport/rss.xml","name":"BBC رياضة ⚽"},
    {"url":"https://www.goal.com/ar/rss","name":"Goal عربي ⚽"},
    {"url":"https://www.kooora.com/rss.aspx","name":"كووورة ⚽"},
    {"url":"https://www.beinsports.com/ar/rss","name":"beIN SPORTS 🌍"},
    {"url":"https://www.filgoal.com/rss.xml","name":"FilGoal ⚽"},
]

POLITICS=[
    {"url":"https://www.bbc.com/arabic/index.xml","name":"BBC عربي 🌍"},
    {"url":"https://www.aljazeera.net/xml/rss/all.xml","name":"الجزيرة 🌍"},
    {"url":"https://sana.sy/feed/","name":"سانا 🇸🇾"},
    {"url":"https://www.france24.com/ar/rss","name":"France24 🇫🇷"},
    {"url":"https://arabic.rt.com/rss/","name":"RT عربي 🇷🇺"},
    {"url":"https://www.skynewsarabia.com/web/rss","name":"سكاي نيوز 🇦🇪"},
    {"url":"https://www.alarabiya.net/.mrss/ar.xml","name":"العربية 🌍"},
]

ECONOMY=[
    {"url":"https://www.aljazeera.net/xml/rss/all.xml","name":"الجزيرة اقتصاد 💰"},
    {"url":"https://www.cnbcarabia.com/feed/","name":"CNBC عربية 💰"},
    {"url":"https://www.bbc.com/arabic/business/rss.xml","name":"BBC اقتصاد 💰"},
    {"url":"https://www.skynewsarabia.com/web/rss?tag=economy","name":"سكاي اقتصاد 💰"},
    {"url":"https://arabic.rt.com/rss/business/","name":"RT اقتصاد 💰"},
]

ART=[
    {"url":"https://www.bbc.com/arabic/arts_and_culture/rss.xml","name":"BBC فن وثقافة 🎭"},
    {"url":"https://www.aljazeera.net/xml/rss/culture.xml","name":"الجزيرة ثقافة 🎭"},
    {"url":"https://www.france24.com/ar/tag/ثقافة/rss","name":"France24 فن 🎭"},
    {"url":"https://www.skynewsarabia.com/web/rss?tag=culture","name":"سكاي فن 🎭"},
    {"url":"https://www.etbilarabi.com/rss","name":"ET بالعربي 🎬"},
]

GENERAL=[
    {"url":"https://news.google.com/rss/search?q=سوريا&hl=ar&gl=SA&ceid=SA:ar","name":"أخبار سوريا 🇸🇾"},
    {"url":"https://www.bbc.com/arabic/index.xml","name":"BBC 🌍"},
    {"url":"https://www.aljazeera.net/xml/rss/all.xml","name":"الجزيرة 🌍"},
]

FEEDS = {
    "الكل":"GENERAL",
    "عاجل 🔴":"POLITICS",
    "رياضة ⚽":"SPORTS",
    "سياسة 🏛️":"POLITICS",
    "اقتصاد 💰":"ECONOMY",
    "فن 🎭":"ART",
    "أسعار 💱":"PRICES",
}

EXTRA={
    "الكل": GENERAL,
    "عاجل 🔴": POLITICS[:4],
    "رياضة ⚽": SPORTS, # 6 مصادر رياضة فقط
    "سياسة 🏛️": POLITICS, # 7 مصادر سياسة فقط
    "اقتصاد 💰": ECONOMY, # 5 مصادر اقتصاد فقط
    "فن 🎭": ART, # 5 مصادر فن جديدة
    "أسعار 💱": []
}

DEFAULT_IMG="https://images.unsplash.com/photo-1495020689067-958852a7765e?w=600"
CACHE={}; CACHE_TIME={}; TRANS={}; PCACHE={"data":None,"time":0}; DCACHE={"data":None,"time":0}

def get_real_prices():
    now=time.time()
    if PCACHE["data"] and now-PCACHE["time"]<30: return PCACHE["data"]
    try:
        syp=load_data().get("syp_black",15250)
        c=requests.get("https://api.coingecko.com/api/v3/simple/price?ids=bitcoin,ethereum&vs_currencies=usd",headers=HEADERS,timeout=5).json()
        data={"btc":f"${c.get('bitcoin',{}).get('usd',84000):,.0f}","eth":f"${c.get('ethereum',{}).get('usd',2688):,.0f}","gold":"$4,286","syp_black":f"{syp:,}","updated":datetime.now().strftime("%H:%M")}
        PCACHE["data"]=data; PCACHE["time"]=now; return data
    except:
        syp=load_data().get("syp_black",15250)
        return {"btc":"$84k","eth":"$2,688","gold":"$4,286","syp_black":f"{syp:,}","updated":datetime.now().strftime("%H:%M")}

def get_detailed_prices():
    now=time.time()
    if DCACHE["data"] and now-DCACHE["time"]<60: return DCACHE["data"]
    try:
        syp_rate=load_data().get("syp_black",15250)
        fx=requests.get("https://api.exchangerate-api.com/v4/latest/USD",headers=HEADERS,timeout=5).json()
        rates=fx.get("rates",{}); TRY=rates.get("TRY",34.2)
        cr=requests.get("https://api.coingecko.com/api/v3/simple/price?ids=bitcoin,ethereum,solana&vs_currencies=usd&include_24hr_change=true",headers=HEADERS,timeout=5).json()
        currencies=[
            {"name":"السورية 🇸🇾","from":f"1$ = {syp_rate:,} ل.س","to":f"1 TL = {syp_rate/TRY:,.0f} ل.س"},
            {"name":"التركية 🇹🇷","from":f"1$ = {TRY:.2f} TL","to":f"1 TL = {syp_rate/TRY:,.0f} ل.س"},
            {"name":"السعودي 🇸🇦","from":f"1$ = {rates.get('SAR',3.75):.2f}","to":f"1 ر.س = {syp_rate/rates.get('SAR',3.75):,.0f} ل.س"},
            {"name":"اليورو 🇪🇺","from":f"1$ = {rates.get('EUR',0.92):.3f}","to":f"1 € = {syp_rate/rates.get('EUR',0.92):,.0f} ل.س"},
        ]
        data={"currencies":currencies,"gold":{"usd_g":138,"usd_oz":4286,"syp_g":int(4286/31.1035*syp
