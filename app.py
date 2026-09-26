from flask import Flask, request, jsonify, redirect, Response
import feedparser, urllib.parse, re, os, json, time, concurrent.futures, requests
from datetime import datetime
app = Flask(__name__)
DATA_FILE = "shami_data.json"
def load_data():
    try:
        with open(DATA_FILE,"r") as f: return json.load(f)
    except: return {"syp_black":15250}
def save_data(d):
    try:
        with open(DATA_FILE,"w") as f: json.dump(d,f)
    except: pass
FEEDS = {"الكل":"https://news.google.com/rss/search?q=سوريا&hl=ar&gl=SA&ceid=SA:ar","عاجل 🔴":"https://news.google.com/rss/search?q=عاجل+سوريا&hl=ar&gl=SA&ceid=SA:ar","رياضة ⚽":"https://www.yallakora.com/rss/rss.aspx","أسعار 💱":"PRICES","اقتصاد 💰":"https://news.google.com/rss/search?q=اقتصاد+سوريا&hl=ar&gl=SA&ceid=SA:ar","سياسة 🏛️":"https://www.bbc.com/arabic/index.xml"}
SPORTS=[{"url":"https://www.yallakora.com/rss/rss.aspx","name":"يلا كورة ⚽"},{"url":"https://www.beinsports.com/ar/rss","name":"beIN 🌍"},{"url":"https://sana.sy/feed/","name":"سانا 🇸🇾"}]
POLITICS=[{"url":"https://www.bbc.com/arabic/index.xml","name":"BBC 🌍"},{"url":"https://www.aljazeera.net/xml/rss/all.xml","name":"الجزيرة 🌍"},{"url":"https://sana.sy/feed/","name":"سانا 🇸🇾"}]
EXTRA={"الكل":POLITICS[:2]+SPORTS[:2],"عاجل 🔴":POLITICS[:3],"رياضة ⚽":SPORTS,"سياسة 🏛️":POLITICS,"اقتصاد 💰":[{"url":"https://www.aljazeera.net/xml/rss/all.xml","name":"اقتصاد"}],"أسعار 💱":[]}
DEFAULT_IMG="https://images.unsplash.com/photo-1495020689067-958852a7765e?w=600"
CACHE={}; CACHE_TIME={}; TRANS={}; PCACHE={"data":None,"time":0}; DCACHE={"data":None,"time":0}

def get_real_prices():
    now=time.time()
    if PCACHE["data"] and now-PCACHE["time"]<60: return PCACHE["data"]
    try:
        syp=load_data().get("syp_black",15250)
        c=requests.get("https://api.coingecko.com/api/v3/simple/price?ids=bitcoin,ethereum&vs_currencies=usd",timeout=5).json()
        g=requests.get("https://api.gold-api.com/price/XAU",timeout=5).json()
        gold=g.get("price",4286) if isinstance(g,dict) else 4286
        data={"btc":f"${c.get('bitcoin',{}).get('usd',67200):,.0f}","eth":f"${c.get('ethereum',{}).get('usd',3800):,.0f}","gold":f"${gold:,.0f}","syp_black":f"{syp:,}","updated":datetime.now().strftime("%H:%M:%S")}
        PCACHE["data"]=data; PCACHE["time"]=now; return data
    except:
        syp=load_data().get("syp_black",15250)
        return {"btc":"$67,200","eth":"$3,800","gold":"$4,286","syp_black":f"{syp:,}","updated":datetime.now().strftime("%H:%M:%S")}

def get_detailed_prices():
    now=time.time()
    if DCACHE["data"] and now-DCACHE["time"]<120: return DCACHE["data"]
    try:
        syp_rate=load_data().get("syp_black",15250)
        fx=requests.get("https://api.exchangerate-api.com/v4/latest/USD",timeout=5).json()
        rates=fx.get("rates",{}); gd=requests.get("https://api.gold-api.com/price/XAU",timeout=5).json(); sd=requests.get("https://api.gold-api.com/price/XAG",timeout=5).json()
        gold_oz=gd.get("price",4286) if isinstance(gd,dict) else 4286; silver_oz=sd.get("price",31.5) if isinstance(sd,dict) else 31.5
        cr=requests.get("https://api.coingecko.com/api/v3/simple/price?ids=bitcoin,ethereum,solana,dash,binancecoin,tether&vs_currencies=usd&include_24hr_change=true",timeout=5).json()
        OZ=31.1035; gg=gold_oz/OZ; gk=gg*1000; sg=silver_oz/OZ
        TRY=rates.get("TRY",34.2)
        def to_syp(x): return x*syp_rate
        def to_try(x): return x*TRY
        currencies=[{"name":"السورية 🇸🇾","from":f"1$ = {syp_rate:,} ل.س","to":f"1 ل.س = ${1/syp_rate:.6f}"},{"name":"التركية 🇹🇷","from":f"1$ = {TRY:.2f} TL","to":f"1 TL = ${1/TRY:.4f}"},{"name":"السعودي 🇸🇦","from":f"1$ = {rates.get('SAR',3.75):.2f} ر.س","to":f"1 ر.س = ${1/rates.get('SAR',3.75):.4f}"},{"name":"اليورو 🇪🇺","from":f"1$ = {rates.get('EUR',0.92):.3f} €","to":f"1 € = ${1/rates.get('EUR',0.92):.3f}"},{"name":"الكويتي 🇰🇼","from":f"1$ = {rates.get('KWD',0.307):.3f} د.ك","to":f"1 د.ك = ${1/rates.get('KWD',0.307):.2f}"},{"name":"المغربي 🇲🇦","from":f"1$ = {rates.get('MAD',9.8):.2f} د.م","to":f"1 د.م = ${1/rates.get('MAD',9.8):.4f}"},{"name":"الجزائري 🇩🇿","from":f"1$ = {rates.get('DZD',134):.1f} د.ج","to":f"1 د.ج = ${1/rates.get('DZD',134):.5f}"},{"name":"المصري 🇪🇬","from":f"1$ = {rates.get('EGP',50.5):.2f} جنيه","to":f"1 جنيه = ${1/rates.get('EGP',50.5):.4f}"}]
        data={"currencies":currencies,"gold":{"usd_g":gg,"usd_oz":gold_oz,"usd_kg":gk,"syp_g":to_syp(gg),"syp_oz":to_syp(gold_oz),"try_g":to_try(gg)},"silver":{"usd_g":sg,"usd_oz":silver_oz,"syp_g":to_syp(sg),"try_g":to_try(sg)},"crypto":[{"n":"Bitcoin ₿","s":"BTC","p":cr.get("bitcoin",{}).get("usd",67200),"c":cr.get("bitcoin",{}).get("usd_24h_change",0)},{"n":"Ethereum ♦","s":"ETH","p":cr.get("ethereum",{}).get("usd",3800),"c":cr.get("ethereum",{}).get("usd_24h_change",0)},{"n":"Solana ◎","s":"SOL","p":cr.get("solana",{}).get("usd",145),"c":cr.get("solana",{}).get("usd_24h_change",0)},{"n":"BNB","s":"BNB","p":cr.get("binancecoin",{}).get("usd",620),"c":cr.get("binancecoin",{}).get("usd_24h_change",0)},{"n":"USDT 💵","s":"USDT","p":cr.get("tether",{}).get("usd",1),"c":0}],"updated":datetime.now().strftime("%H:%M:%S")}
        DCACHE["data"]=data; DCACHE["time"]=now; return data
    except:
        return {"currencies":[{"name":"السورية 🇸🇾","from":"1$ = 15,250 ل.س","to":"1 ل.س = $0.000065"}],"gold":{"usd_g":137,"usd_oz":4286,"usd_kg":137700,"syp_g":2090000,"syp_oz":65361500,"try_g":4710},"silver":{"usd_g":1.01,"usd_oz":31.5,"syp_g":15400,"try_g":34},"crypto":[{"n":"BTC","s":"BTC","p":67200,"c":1}],"updated":datetime.now().strftime("%H:%M:%S")}

def trans_ar(t):
    if re.search(r'[\u0600-\u06FF]',t): return t
    if t in TRANS: return TRANS[t]
    try:
        url=f"https://translate.googleapis.com/translate_a/single?client=gtx&sl=auto&tl=ar&dt=t&q={urllib.parse.quote(t)}"
        r=requests.get(url,timeout=3).json(); tr="".join([s[0] for s in r[0]]); TRANS[t]=tr; return tr
    except: return t
def get_img(e):
    try:
        if hasattr(e,'media_content') and e.media_content:
            u=e.media_content[0].get('url',''); 
            if u.startswith('http'): return u
    except: pass
    m=re.search(r'<img[^>]+src="([^"]+)"', getattr(e,'description',''))
    if m: return m.group(1)
    return None
def get_og(u):
    try:
        r=requests.get(u, headers={'User-Agent':'Mozilla/5.0'}, timeout=3)
        m=re.search(r'property="og:image"[^>]+content="([^"]+)"', r.text, re.I)
        if m: return m.group(1)
    except: pass
    return None
def fetch_one(args):
    src,cat=args
    try:
        f=feedparser.parse(src["url"]); res=[]
        for e in f.entries[:4]:
            img=get_img(e) or get_og(e.link) or DEFAULT_IMG
            title=trans_ar(e.title)
            res.append({"title":title,"link":e.link,"time":getattr(e,'published','')[:16],"source":src["name"],"image":img})
        return res
    except: return []
def get_news(cat,q=None):
    now=time.time(); key=f"{cat}_{q or ''}"
    if key in CACHE and now-CACHE_TIME.get(key,0)<180: return CACHE[key]
    if q:
        try:
            feed=feedparser.parse(f"https://news.google.com/rss/search?q={urllib.parse.quote(q)}&hl=ar&gl=SA&ceid=SA:ar"); res=[]
            for e in feed.entries[:12]:
                img=get_img(e) or get_og(e.link) or DEFAULT_IMG
                res.append({"title":trans_ar(e.title),"link":e.link,"time":getattr(e,'published','')[:16],"source":"بحث 🔍","image":img})
            CACHE[key]=res; CACHE_TIME[key]=now; return res
        except: return []
    all_news=[]; sources=EXTRA.get(cat,[])[:5]
    if sources:
        with concurrent.futures.ThreadPoolExecutor(max_workers=5) as ex:
            results=list(ex.map(fetch_one, [(s,cat) for s in sources]))
            for r in results: all_news.extend(r)
    try:
        if FEEDS.get(cat) and FEEDS.get(cat)!="PRICES":
            fg=feedparser.parse(FEEDS.get(cat))
            for e in fg.entries[:2]:
                img=get_img(e) or get_og(e.link) or DEFAULT_IMG
                all_news.append({"title":trans_ar(e.title),"link":e.link,"time":getattr(e,'published','')[:16],"source":"Google","image":img})
    except: pass
    CACHE[key]=all_news[:25]; CACHE_TIME[key]=now; return all_news[:25]

@app.route('/manifest.json')
def manifest(): return jsonify({"name":"شامي","short_name":"شامي","start_url":"/","display":"standalone","background_color":"#1b5e20","theme_color":"#1b5e20","icons":[{"src":"https://cdn-icons-png.flaticon.com/512/21/21601.png","sizes":"512x512","type":"image/png"}]})
@app.route('/sw.js')
def sw(): return Response("self.addEventListener('install',e=>self.skipWaiting());", mimetype='application/javascript')
@app.route('/api/prices')
def api_prices(): return jsonify(get_real_prices())
@app.route('/admin', methods=['GET','POST'])
def admin():
    if request.method=='POST':
        try:
            syp=int(request.form.get('syp','15250').replace(',','')); save_data({"syp_black":syp}); PCACHE["time"]=0; DCACHE["time"]=0
        except: pass
        return redirect('/admin')
    data=load_data()
    return f'<html dir="rtl"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>لوحة تحكم</title><style>body{{font-family:Tajawal;padding:20px;background:#f5f5f5}}.box{{background:#fff;padding:20px;border-radius:12px;max-width:500px;margin:auto}}input{{width:100%;padding:12px;border:1px solid #ddd;border-radius:8px;margin:10px 0}}button{{background:#1b5e20;color:#fff;border:0;padding:12px;border-radius:8px;width:100%;font-weight:800}}</style></head><body><div class="box"><h2>🔧 لوحة تحكم شامي</h2><form method="post"><label>سعر الدولار</label><input name="syp" value="{data.get("syp_black",15250)}"><button>حفظ ✅</button></form><br><a href="/">رجوع</a></div></body></html>'

def prices_page():
    d=get_detailed_prices()
    tabs="".join([f'<a href="/?cat={urllib.parse.quote(k)}" class="tab {"active" if k=="أسعار 💱" else ""}">{k}</a>' for k in FEEDS])
    curr="".join([f'<tr><td><b>{c["name"]}</b></td><td>{c["from"]}</td><td style="color:#1b5e20">{c["to"]}</td></tr>' for c in d["currencies"]])
    crypto="".join([f'<div class="c-card"><div><b>{c["n"]}</b> {c["s"]}</div><div><b>${c["p"]:,.2f}</b> <small style="color:{"#25D366" if c["c"]>=0 else "#e53935"}">{c["c"]:.2f}%</small></div></div>' for c in d["crypto"]])
    g=d["gold"]; s=d["silver"]
    return f'''<!doctype html><html dir="rtl"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>أسعار</title><link href="https://fonts.googleapis.com/css2?family=Tajawal:wght@700&display=swap" rel="stylesheet"><style>*{{font-family:Tajawal;box-sizing:border-box}}body{{margin:0;background:#f2f3f5}}.top{{background:#1b5e20;color:#fff;padding:12px}} .tabs{{display:flex;gap:10px;overflow:auto;padding:12px;background:#fff}} .tab{{padding:10px 18px;background:#eceff1;border-radius:24px;text-decoration:none;color:#333;font-weight:700;font-size:13px;white-space:nowrap}} .tab.active{{background:#1b5e20;color:#fff}} .container{{max-width:800px;margin:auto;padding:12px}} .sec{{background:#fff;border-radius:16px;padding:14px;margin:14px 0}} table{{width:100%;border-collapse:collapse;font-size:13px}} th{{background:#f5f5f5;padding:10px;text-align:right}} td{{padding:10px;border-bottom:1px solid #eee}} .grid{{display:grid;grid-template-columns:1fr 1fr 1fr;gap:8px}} .box{{background:#f8f9f8;border:1px solid #eee;border-radius:12px;padding:10px;text-align:center}} .c-card{{display:flex;justify-content:space-between;background:#fafafa;border:1px solid #eee;border-radius:12px;padding:12px;margin:6px 0}}</style></head><body><div class="top"><h2 style="margin:0">💱 أسعار شامي - {d["updated"]}</h2></div><div class="tabs">{tabs}</div><div class="container"><div class="sec"><h3>💵 العملات</h3><table><tr><th>العملة</th><th>من الدولار</th><th>إلى الدولار</th></tr>{curr}</table></div><div class="sec"><h3>🪙 الذهب</h3><div class="grid"><div class="box"><small>جرام $</small><b>${g["usd_g"]:.2f}</b></div><div class="box"><small>أونصة $</small><b>${g["usd_oz"]:.0f}</b></div><div class="box"><small>كيلو $</small><b>${g["usd_kg"]:.0f}</b></div></div><br><div class="grid"><div class="box"><small>جرام سوري</small><b>{g["syp_g"]:,.0f}</b></div><div class="box"><small>أونصة سوري</small><b>{g["syp_oz"]:,.0f}</b></div><div class="box"><small>جرام تركي</small><b>{g["try_g"]:.0f} TL</b></div></div></div><div class="sec"><h3>🥈 الفضة</h3><div class="grid"><div class="box"><small>جرام $</small><b>${s["usd_g"]:.2f}</b></div><div class="box"><small>أونصة $</small><b>${s["usd_oz"]:.2f}</b></div><div class="box"><small>جرام سوري</small><b>{s["syp_g"]:,.0f}</b></div></div></div><div class="sec"><h3>₿ كريبتو</h3>{crypto}</div></div></body></html>'''

def home_render(cat,news,q=None):
    if cat=="أسعار 💱": return prices_page()
    prices=get_real_prices()
    try:
        urgent=get_news("عاجل 🔴")[:5]; ticker=" 🔴 ".join([n["title"] for n in urgent])
    except: ticker="أخبار عاجلة - شامي"
    tabs="".join([f'<a href="/?cat={urllib.parse.quote(k)}" class="tab {"active" if k==cat and not q else ""}">{k}</a>' for k in FEEDS])
    cards=""
    for n in news:
        cards+=f'<div class="card"><div class="imgw"><img src="{n["image"]}" loading="lazy" onerror="this.src=\'{DEFAULT_IMG}\'"><span class="badge">{n["source"]}</span></div><div class="info"><small>{n["time"]}</small><h2>{n["title"]}</h2><div class="btns"><a href="{n["link"]}" target="_blank" class="btn-r">📖 اقرأ</a><a href="https://wa.me/?text={urllib.parse.quote(n["title"]+" "+n["link"])}" target="_blank" class="btn-w">واتساب</a></div></div></div>'
    return f'''<!doctype html><html dir="rtl"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>شامي</title><link rel="manifest" href="/manifest.json"><link href="https://fonts.googleapis.com/css2?family=Tajawal:wght@700;800&display=swap" rel="stylesheet"><style>*{{font-family:Tajawal;box-sizing:border-box}}body{{margin:0;background:#f2f3f5}} .top{{background:#1b5e20;color:#fff;padding:12px;display:flex;justify-content:space-between;align-items:center;position:sticky;top:0;z-index:30}} .ticker{{background:#d32f2f;color:#fff;display:flex;align-items:center;height:44px;overflow:hidden}} .label{{background:#fff;color:#d32f2f;font-weight:900;padding:6px 14px;border-radius:6px;margin:0 10px;white-space:nowrap}} .prices{{background:#0e0e0e;color:#ddd;display:flex;gap:16px;overflow:auto;padding:9px 12px;font-size:13px;white-space:nowrap}} .tabs{{display:flex;gap:10px;overflow:auto;padding:12px;background:#fff;position:sticky;top:56px;z-index:20}} .tab{{padding:10px 18px;background:#eceff1;border-radius:24px;text-decoration:none;color:#333;font-weight:700;font-size:13px;white-space:nowrap}} .tab.active{{background:#1b5e20;color:#fff}} .container{{max-width:760px;margin:auto;padding:12px}} .card{{background:#fff;border-radius:18px;overflow:hidden;margin:14px 0;box-shadow:0 4px 12px rgba(0,0,0,.08)}} .imgw{{position:relative}} .imgw img{{width:100%;height:230px;object-fit:cover}} .badge{{position:absolute;top:12px;right:12px;background:rgba(0,0,0,.7);color:#fff;padding:5px 10px;border-radius:20px;font-size:11px}} .info{{padding:14px}} .info h2{{margin:6px 0 12px;font-size:16px;line-height:1.5}} .btns{{display:flex;gap:10px}} .btn-r,.btn-w{{flex:1;text-align:center;padding:12px;border-radius:12px;text-decoration:none;font-weight:800}} .btn-r{{background:#111;color:#fff}} .btn-w{{background:#25D366;color:#fff}} .search{{background:#fff;padding:10px;position:sticky;top:108px;z-index:19}} .search form{{max-width:760px;margin:auto;display:flex;gap:8px}} .search input{{flex:1;padding:12px 16px;border:1px solid #ddd;border-radius:24px}} .search button{{background:#1b5e20;color:#fff;border:0;padding:12px 20px;border-radius:24px;font-weight:800}}</style></head><body><div class="top"><div><b>🔥 شامي</b><br><small style="font-size:11px;opacity:.8">أخبار + أسعار حية</small></div><div><a href="/admin" style="background:rgba(255,255,255,.2);color:#fff;padding:8px 12px;border-radius:20px;text-decoration:none">⚙️</a></div></div><div class="ticker"><span class="label">عاجل 🔴</span><marquee scrollamount="7" direction="right">{ticker}</marquee></div><div class="prices"><span>₿ {prices["btc"]}</span><span>ETH {prices["eth"]}</span><span>🪙 {prices["gold"]}</span><span>💵 دمشق {prices["syp_black"]} ل.س</span><span style="margin-right:auto"><a href="/?cat=%D8%A3%D8%B3%D8%B9%D8%A7%D8%B1%20%F0%9F%92%B1" style="color:#25D366;text-decoration:none;font-weight:800">كل الأسعار 💱</a></span></div><div class="search"><form action="/search"><input name="q" value="{q or ''}" placeholder="🔍 ابحث..."><button>بحث</button></form></div><div class="tabs">{tabs}</div><div class="container">{cards}</div></body></html>'''

@app.route('/search')
def search():
    q=request.args.get('q','').strip()
    if not q: return redirect('/')
    return home_render("الكل", get_news("الكل", q=q), q)
@app.route('/')
def home():
    cat=request.args.get('cat','الكل')
    return home_render(cat, get_news(cat) if cat!="أسعار 💱" else [])
if __name__=='__main__':
    app.run(host='0.0.0.0',port=int(os.environ.get("PORT",10000)))
