from flask import Flask, request, jsonify, redirect, Response
import feedparser, urllib.parse, re, os, json, time, concurrent.futures, requests
from datetime import datetime
app = Flask(__name__)
DATA_FILE="shami_data.json"
HEADERS={'User-Agent':'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}

def load_data():
    try:
        with open(DATA_FILE,"r") as f: return json.load(f)
    except: return {"syp_black":15250}
def save_data(d):
    with open(DATA_FILE,"w") as f: json.dump(d,f)

# كل مصادرك القديمة رجعت - ما حذفنا شي
SPORTS=[
    {"url":"https://www.yallakora.com/rss/rss.aspx","name":"يلا كورة ⚽"},
    {"url":"https://www.beinsports.com/ar/rss","name":"beIN SPORTS 🌍"},
    {"url":"https://www.kooora.com/rss.aspx","name":"كووورة ⚽"},
    {"url":"https://www.bbc.com/arabic/sport/rss.xml","name":"BBC رياضة"},
]

POLITICS=[
    {"url":"https://www.bbc.com/arabic/index.xml","name":"BBC عربي 🌍"},
    {"url":"https://www.aljazeera.net/xml/rss/all.xml","name":"الجزيرة 🌍"},
    {"url":"https://sana.sy/feed/","name":"سانا 🇸🇾"},
    {"url":"https://www.alarabiya.net/.mrss/ar.xml","name":"العربية 🌍"},
]

GENERAL=[
    {"url":"https://news.google.com/rss/search?q=سوريا&hl=ar&gl=SA&ceid=SA:ar","name":"Google سوريا 🇸🇾"},
    {"url":"https://www.aljazeera.net/xml/rss/all.xml","name":"الجزيرة 🌍"},
    {"url":"https://www.bbc.com/arabic/index.xml","name":"BBC 🌍"},
]

DEFAULT_IMG="https://images.unsplash.com/photo-1495020689067-958852a7765e?w=600"
CACHE={}; CACHE_TIME={}; PCACHE={"data":None,"time":0}; DCACHE={"data":None,"time":0}

def get_real_prices():
    now=time.time()
    if PCACHE["data"] and now-PCACHE["time"]<30: return PCACHE["data"]
    try:
        syp=load_data().get("syp_black",15250)
        r=requests.get("https://api.coingecko.com/api/v3/simple/price?ids=bitcoin,ethereum&vs_currencies=usd",headers=HEADERS,timeout=4).json()
        data={"btc":f"${r.get('bitcoin',{}).get('usd',84165):,.0f}","eth":f"${r.get('ethereum',{}).get('usd',2690):,.0f}","gold":"$4,286","syp_black":f"{syp:,}","updated":datetime.now().strftime("%H:%M")}
        PCACHE["data"]=data; PCACHE["time"]=now; return data
    except:
        syp=load_data().get("syp_black",15250)
        return {"btc":"$84,165","eth":"$2,690","gold":"$4,286","syp_black":f"{syp:,}","updated":datetime.now().strftime("%H:%M")}

def get_detailed():
    now=time.time()
    if DCACHE["data"] and now-DCACHE["time"]<60: return DCACHE["data"]
    try:
        syp_rate=load_data().get("syp_black",15250)
        fx=requests.get("https://api.exchangerate-api.com/v4/latest/USD",headers=HEADERS,timeout=5).json()
        rates=fx.get("rates",{}); TRY=rates.get("TRY",34.5)
        cr=requests.get("https://api.coingecko.com/api/v3/simple/price?ids=bitcoin,ethereum,solana&vs_currencies=usd&include_24hr_change=true",headers=HEADERS,timeout=5).json()
        currencies=[
            {"name":"السورية السوداء 🇸🇾","from":f"1$ = {syp_rate:,} ل.س","to":f"1 TL = {syp_rate/TRY:,.0f} ل.س","hl":True},
            {"name":"التركية 🇹🇷","from":f"1$ = {TRY:.2f} TL","to":f"1 TL = {syp_rate/TRY:,.0f} ل.س"},
            {"name":"السعودي 🇸🇦","from":f"1$ = {rates.get('SAR',3.75):.2f}","to":f"1 ر.س = {syp_rate/rates.get('SAR',3.75):,.0f} ل.س"},
            {"name":"اليورو 🇪🇺","from":f"1$ = {rates.get('EUR',0.92):.3f}","to":f"1 € = {syp_rate/rates.get('EUR',0.92):,.0f} ل.س"},
        ]
        data={"currencies":currencies,"gold":{"oz":4286,"g_syp":int(4286/31.1035*syp_rate)},"crypto":[{"n":"BTC","p":cr.get("bitcoin",{}).get("usd",84165),"c":0}],"updated":datetime.now().strftime("%H:%M:%S")}
        DCACHE["data"]=data; DCACHE["time"]=now; return data
    except:
        syp=load_data().get("syp_black",15250)
        return {"currencies":[{"name":"السورية 🇸🇾","from":f"1$ = {syp:,}","to":""}],"gold":{"oz":4286,"g_syp":2090000},"crypto":[],"updated":datetime.now().strftime("%H:%M:%S")}

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
        resp=requests.get(src["url"], headers=HEADERS, timeout=8)
        if resp.status_code!=200: return []
        f=feedparser.parse(resp.content)
        res=[]
        for en in f.entries[:10]:
            res.append({"title":en.title,"link":en.link,"time":getattr(en,'published','')[:16],"source":src["name"],"image":get_img(en)})
        return res
    except Exception as e:
        print(f"Failed {src['url']}: {e}")
        return []

def get_news(cat):
    now=time.time()
    if cat in CACHE and now-CACHE_TIME.get(cat,0)<300: return CACHE[cat]
    all_news=[]
    try:
        if cat=="رياضة ⚽":
            with concurrent.futures.ThreadPoolExecutor(max_workers=4) as ex:
                for r in ex.map(fetch_one, SPORTS): all_news.extend(r)
        elif cat=="سياسة 🏛️":
            with concurrent.futures.ThreadPoolExecutor(max_workers=4) as ex:
                for r in ex.map(fetch_one, POLITICS): all_news.extend(r)
        elif cat=="أسعار 💱":
            all_news=[]
        else:
            with concurrent.futures.ThreadPoolExecutor(max_workers=4) as ex:
                for r in ex.map(fetch_one, GENERAL): all_news.extend(r)
    except: pass

    if not all_news and cat in CACHE:
        return CACHE[cat]
    # لو فشل كلشي - لا ترجع فاضي
    if not all_news:
        all_news=[{"title":f"لا يوجد أخبار حالياً في قسم {cat} - جرب تحديث الصفحة","link":"/","time":datetime.now().strftime("%H:%M"),"source":"شامي","image":DEFAULT_IMG}]

    CACHE[cat]=all_news[:30]; CACHE_TIME[cat]=now
    return CACHE[cat]

@app.route('/manifest.json')
def mani(): return jsonify({"name":"شامي","short_name":"شامي","start_url":"/","display":"standalone","background_color":"#1b5e20","theme_color":"#1b5e20","icons":[{"src":"https://cdn-icons-png.flaticon.com/512/21/21601.png","sizes":"512x512","type":"image/png"}]})
@app.route('/sw.js')
def sw(): return Response("self.addEventListener('install',e=>self.skipWaiting());", mimetype='application/javascript')
@app.route('/api/prices')
def api_p(): return jsonify(get_real_prices())
@app.route('/api/prices/detailed')
def api_d(): return jsonify(get_detailed())
@app.route('/admin', methods=['GET','POST'])
def admin():
    if request.method=='POST':
        try: save_data({"syp_black":int(request.form.get('syp','15250').replace(',',''))}); PCACHE["time"]=0; DCACHE["time"]=0
        except: pass
        return redirect('/admin')
    syp=load_data().get("syp_black",15250)
    return f'<html dir="rtl"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><style>body{{font-family:system-ui;padding:20px;background:#f5f5f5}}.box{{background:#fff;padding:20px;border-radius:12px;max-width:400px;margin:auto}}input{{width:100%;padding:12px}}button{{width:100%;padding:12px;background:#1b5e20;color:#fff;border:0;border-radius:8px;margin-top:10px}}</style></head><body><div class="box"><h3>🔧 سعر $ دمشق</h3><form method="post"><input name="syp" value="{syp}"><button>حفظ ✅</button></form><br><a href="/">رجوع</a></div></body></html>'

@app.route('/')
def home():
    cat=request.args.get('cat','الكل')
    prices=get_real_prices()
    tabs="".join([f'<a href="/?cat={urllib.parse.quote(k)}" class="tab {"active" if k==cat else ""}">{k}</a>' for k in ["الكل","عاجل 🔴","رياضة ⚽","سياسة 🏛️","أسعار 💱"]])
    if cat=="أسعار 💱":
        d=get_detailed()
        rows="".join([f'<tr style="{"background:#e8f5e9" if c.get("hl") else ""}"><td><b>{c["name"]}</b></td><td>{c["from"]}</td><td style="color:#1b5e20;font-weight:800">{c["to"]}</td></tr>' for c in d["currencies"]])
        return f'''<!doctype html><html dir="rtl"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>أسعار شامي</title><link href="https://fonts.googleapis.com/css2?family=Tajawal:wght@700&display=swap" rel="stylesheet"><style>*{{font-family:Tajawal;box-sizing:border-box}}body{{margin:0;background:#f2f3f5}}.top{{background:#1b5e20;color:#fff;padding:12px;display:flex;justify-content:space-between}}.tabs{{display:flex;gap:8px;overflow:auto;padding:10px;background:#fff}}.tab{{padding:10px 16px;background:#eceff1;border-radius:20px;text-decoration:none;color:#333;font-size:13px;white-space:nowrap}}.tab.active{{background:#1b5e20;color:#fff}}.box{{max-width:800px;margin:auto;padding:12px}}.sec{{background:#fff;border-radius:14px;padding:14px;margin:12px 0}} table{{width:100%;border-collapse:collapse;font-size:13px}} td,th{{padding:10px;border-bottom:1px solid #eee;text-align:right}}</style></head><body><div class="top"><b>💱 أسعار {d["updated"]}</b><a href="/" style="color:#fff">رجوع ⬅️</a></div><div class="tabs">{tabs}</div><div class="box"><div class="sec"><table><tr><th>العملة</th><th>السعر</th><th>بالسوري</th></tr>{rows}</table></div></div></body></html>'''
    news=get_news(cat)
    cards="".join([f'<div class="card"><div class="imgw"><img src="{n["image"]}" loading="lazy" onerror="this.src=\'{DEFAULT_IMG}\'"><span class="badge">{n["source"]}</span></div><div class="info"><small>{n["time"]}</small><h2>{n["title"]}</h2><div class="btns"><a href="{n["link"]}" target="_blank" class="btn-r">📖 اقرأ</a><a href="https://wa.me/?text={urllib.parse.quote(n["title"]+" "+n["link"])}" target="_blank" class="btn-w">واتساب</a></div></div></div>' for n in news])
    return f'''<!doctype html><html dir="rtl"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>شامي - {cat}</title><link rel="manifest" href="/manifest.json"><link href="https://fonts.googleapis.com/css2?family=Tajawal:wght@700;800&display=swap" rel="stylesheet"><style>*{{font-family:Tajawal;box-sizing:border-box}}body{{margin:0;background:#f2f3f5}}.top{{background:#1b5e20;color:#fff;padding:12px;display:flex;justify-content:space-between;align-items:center;position:sticky;top:0;z-index:30}}.prices{{background:#111;color:#ddd;display:flex;gap:14px;overflow:auto;padding:9px 12px;font-size:13px;white-space:nowrap}}.tabs{{display:flex;gap:8px;overflow:auto;padding:10px;background:#fff;position:sticky;top:54px;z-index:20}}.tab{{padding:10px 16px;background:#eceff1;border-radius:20px;text-decoration:none;color:#333;font-weight:700;font-size:13px;white-space:nowrap}}.tab.active{{background:#1b5e20;color:#fff}}.container{{max-width:760px;margin:auto;padding:12px}}.card{{background:#fff;border-radius:16px;overflow:hidden;margin:12px 0;box-shadow:0 3px 10px rgba(0,0,0,.07)}}.imgw{{position:relative}}.imgw img{{width:100%;height:220px;object-fit:cover;background:#eee}}.badge{{position:absolute;top:10px;right:10px;background:rgba(0,0,0,.7);color:#fff;padding:4px 8px;border-radius:14px;font-size:11px}}.info{{padding:12px}}.info h2{{margin:6px 0 10px;font-size:15px;line-height:1.5}}.btns{{display:flex;gap:8px}}.btn-r,.btn-w{{flex:1;text-align:center;padding:10px;border-radius:10px;text-decoration:none;font-weight:800;font-size:13px}}.btn-r{{background:#111;color:#fff}}.btn-w{{background:#25D366;color:#fff}}</style></head><body>
<div class="top"><div><b>🔥 شامي</b><br><small style="font-size:11px;opacity:.8">أخبار + أسعار حية</small></div><a href="/admin" style="background:rgba(255,255,255,.2);color:#fff;padding:6px 10px;border-radius:16px;text-decoration:none">⚙️</a></div>
<div class="prices"><span>₿ {prices["btc"]}</span><span>ETH {prices["eth"]}</span><span>🪙 {prices["gold"]}</span><span>💵 دمشق {prices["syp_black"]} ل.س</span><span style="margin-right:auto"><a href="/?cat=%D8%A3%D8%B3%D8%B9%D8%A7%D8%B1%20%F0%9F%92%B1" style="color:#25D366;text-decoration:none">كل الأسعار 💱</a></span></div>
<div class="tabs">{tabs}</div>
<div class="container">{cards}</div>
</body></html>'''

if __name__=='__main__':
    app.run(host='0.0.0.0',port=int(os.environ.get("PORT",10000)))
