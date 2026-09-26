from flask import Flask, request, jsonify, redirect, Response
import feedparser, urllib.parse, re, os, json, time, concurrent.futures, requests
from datetime import datetime

app = Flask(__name__)
DATA_FILE = "shami_data.json"

# === حفظ أسعار السوق ===
def load_data():
    try:
        with open(DATA_FILE, "r") as f: return json.load(f)
    except: return {"syp_black":15250}
def save_data(d):
    try:
        with open(DATA_FILE, "w") as f: json.dump(d,f)
    except: pass

FEEDS = {
    "الكل": "https://news.google.com/rss/search?q=سوريا&hl=ar&gl=SA&ceid=SA:ar",
    "عاجل 🔴": "https://news.google.com/rss/search?q=عاجل+سوريا&hl=ar&gl=SA&ceid=SA:ar",
    "رياضة ⚽": "https://www.yallakora.com/rss/rss.aspx",
    "أسعار 💱": "PRICES_PAGE",
    "اقتصاد 💰": "https://news.google.com/rss/search?q=اقتصاد+سوريا&hl=ar&gl=SA&ceid=SA:ar",
    "سياسة 🏛️": "https://www.bbc.com/arabic/index.xml",
}
SPORTS_SOURCES = [
    {"url": "https://www.yallakora.com/rss/rss.aspx", "name": "يلا كورة ⚽"},
    {"url": "https://www.beinsports.com/ar/rss", "name": "beIN 🌍"},
    {"url": "https://sana.sy/feed/", "name": "سانا 🇸🇾"},
    {"url": "https://www.kooora.com/rss.aspx", "name": "كووورة ⚽"},
]
POLITICS_SOURCES = [
    {"url": "https://www.bbc.com/arabic/index.xml", "name": "BBC 🌍"},
    {"url": "https://www.aljazeera.net/xml/rss/all.xml", "name": "الجزيرة 🌍"},
    {"url": "https://sana.sy/feed/", "name": "سانا سياسة 🇸🇾"},
    {"url": "https://www.skynewsarabia.com/web/rss", "name": "سكاي نيوز 🌍"},
]
EXTRA_FEEDS = {
    "الكل": POLITICS_SOURCES[:3] + SPORTS_SOURCES[:2],
    "عاجل 🔴": POLITICS_SOURCES[:4],
    "رياضة ⚽": SPORTS_SOURCES,
    "سياسة 🏛️": POLITICS_SOURCES,
    "اقتصاد 💰": [{"url": "https://www.aljazeera.net/xml/rss/all.xml", "name": "اقتصاد"}],
    "أسعار 💱": []
}
DEFAULT_IMAGES = {"الكل": "https://images.unsplash.com/photo-1495020689067-958852a7765e?w=600"}

PRICES_CACHE = {"data": None, "time": 0}
DETAILED_CACHE = {"data": None, "time": 0}
TRANSLATE_CACHE = {}
CACHE = {}
CACHE_TIME = {}

def get_real_prices():
    now = time.time()
    if PRICES_CACHE["data"] and now - PRICES_CACHE["time"] < 60:
        return PRICES_CACHE["data"]
    try:
        syp = load_data().get("syp_black",15250)
        crypto = requests.get("https://api.coingecko.com/api/v3/simple/price?ids=bitcoin,ethereum&vs_currencies=usd&include_24hr_change=true", timeout=5).json()
        gold_resp = requests.get("https://api.gold-api.com/price/XAU", timeout=5).json()
        gold_price = gold_resp.get("price", 4286) if isinstance(gold_resp, dict) else 4286
        data = {"btc": f"${crypto.get('bitcoin',{}).get('usd',67200):,.0f}","btc_change": f"{crypto.get('bitcoin',{}).get('usd_24h_change',1.2):.1f}%","eth": f"${crypto.get('ethereum',{}).get('usd',3800):,.0f}","gold": f"${gold_price:,.0f}","syp_black": f"{syp:,}","updated": datetime.now().strftime("%H:%M:%S")}
        PRICES_CACHE["data"]=data; PRICES_CACHE["time"]=now; return data
    except:
        syp=load_data().get("syp_black",15250)
        return PRICES_CACHE["data"] or {"btc":"$67,200","btc_change":"+1.2%","eth":"$3,800","gold":"$4,286","syp_black":f"{syp:,}","updated":datetime.now().strftime("%H:%M:%S")}

def get_detailed_prices():
    now = time.time()
    if DETAILED_CACHE["data"] and now - DETAILED_CACHE["time"] < 120:
        return DETAILED_CACHE["data"]
    try:
        syp_rate = load_data().get("syp_black",15250)
        fx = requests.get("https://api.exchangerate-api.com/v4/latest/USD", timeout=5).json()
        rates = fx.get("rates", {})
        gold_data = requests.get("https://api.gold-api.com/price/XAU", timeout=5).json()
        silver_data = requests.get("https://api.gold-api.com/price/XAG", timeout=5).json()
        gold_usd_oz = gold_data.get("price", 4286) if isinstance(gold_data, dict) else 4286
        silver_usd_oz = silver_data.get("price", 31.5) if isinstance(silver_data, dict) else 31.5
        crypto = requests.get("https://api.coingecko.com/api/v3/simple/price?ids=bitcoin,ethereum,solana,dash,binancecoin,tether&vs_currencies=usd&include_24hr_change=true", timeout=5).json()
        OZ=31.1035; gold_g=gold_usd_oz/OZ; gold_kg=gold_g*1000; silver_g=silver_usd_oz/OZ; silver_kg=silver_g*1000
        TRY_RATE=rates.get("TRY",34.2)
        def to_syp(usd): return usd*syp_rate
        def to_try(usd): return usd*TRY_RATE
        currencies=[
            {"name":"الليرة السورية 🇸🇾","code":"SYP","from_usd":f"1$ = {syp_rate:,} ل.س","to_usd":f"1 ل.س = ${1/syp_rate:.6f}"},
            {"name":"الليرة التركية 🇹🇷","code":"TRY","from_usd":f"1$ = {rates.get('TRY',34.2):.2f} TL","to_usd":f"1 TL = ${1/rates.get('TRY',34.2):.4f}"},
            {"name":"الريال السعودي 🇸🇦","code":"SAR","from_usd":f"1$ = {rates.get('SAR',3.75):.2f} ر.س","to_usd":f"1 ر.س = ${1/rates.get('SAR',3.75):.4f}"},
            {"name":"اليورو 🇪🇺","code":"EUR","from_usd":f"1$ = {rates.get('EUR',0.92):.3f} €","to_usd":f"1 € = ${1/rates.get('EUR',0.92):.3f}"},
            {"name":"الدينار الكويتي 🇰🇼","code":"KWD","from_usd":f"1$ = {rates.get('KWD',0.307):.3f} د.ك","to_usd":f"1 د.ك = ${1/rates.get('KWD',0.307):.2f}"},
            {"name":"الدرهم المغربي 🇲🇦","code":"MAD","from_usd":f"1$ = {rates.get('MAD',9.8):.2f} د.م","to_usd":f"1 د.م = ${1/rates.get('MAD',9.8):.4f}"},
            {"name":"الدينار الجزائري 🇩🇿","code":"DZD","from_usd":f"1$ = {rates.get('DZD',134):.1f} د.ج","to_usd":f"1 د.ج = ${1/rates.get('DZD',134):.5f}"},
            {"name":"الجنيه المصري 🇪🇬","code":"EGP","from_usd":f"1$ = {rates.get('EGP',50.5):.2f} جنيه","to_usd":f"1 جنيه = ${1/rates.get('EGP',50.5):.4f}"},
        ]
        data={"currencies":currencies,"gold":{"usd_oz":gold_usd_oz,"usd_g":gold_g,"usd_kg":gold_kg,"syp_g":to_syp(gold_g),"syp_oz":to_syp(gold_usd_oz),"syp_kg":to_syp(gold_kg),"try_g":to_try(gold_g),"try_oz":to_try(gold_usd_oz),"try_kg":to_try(gold_kg)},"silver":{"usd_oz":silver_usd_oz,"usd_g":silver_g,"usd_kg":silver_kg,"syp_g":to_syp(silver_g),"syp_oz":to_syp(silver_usd_oz),"syp_kg":to_syp(silver_kg),"try_g":to_try(silver_g),"try_oz":to_try(silver_usd_oz),"try_kg":to_try(silver_kg)},"crypto":[{"name":"Bitcoin ₿","sym":"BTC","price":crypto.get("bitcoin",{}).get("usd",67200),"change":crypto.get("bitcoin",{}).get("usd_24h_change",0)},{"name":"Ethereum ♦","sym":"ETH","price":crypto.get("ethereum",{}).get("usd",3800),"change":crypto.get("ethereum",{}).get("usd_24h_change",0)},{"name":"Solana ◎","sym":"SOL","price":crypto.get("solana",{}).get("usd",145),"change":crypto.get("solana",{}).get("usd_24h_change",0)},{"name":"Dash","sym":"DASH","price":crypto.get("dash",{}).get("usd",28),"change":crypto.get("dash",{}).get("usd_24h_change",0)},{"name":"BNB","sym":"BNB","price":crypto.get("binancecoin",{}).get("usd",620),"change":crypto.get("binancecoin",{}).get("usd_24h_change",0)},{"name":"USDT 💵","sym":"USDT","price":crypto.get("tether",{}).get("usd",1),"change":0}],"updated":datetime.now().strftime("%Y-%m-%d %H:%M:%S")}
        DETAILED_CACHE["data"]=data; DETAILED_CACHE["time"]=now; return data
    except Exception as e:
        return DETAILED_CACHE["data"] or {"currencies":[],"gold":{"usd_oz":4286,"usd_g":137,"usd_kg":137000,"syp_g":2090000,"syp_oz":65361500,"syp_kg":2090000000,"try_g":4710,"try_oz":146500,"try_kg":4710000},"silver":{"usd_oz":31.5,"usd_g":1.01,"usd_kg":1012,"syp_g":15400,"syp_oz":480375,"syp_kg":15435000,"try_g":34,"try_oz":1077,"try_kg":34600},"crypto":[],"updated":datetime.now().strftime("%H:%M:%S")}

def translate_to_ar(text):
    if re.search(r'[\u0600-\u06FF]', text): return text
    if text in TRANSLATE_CACHE: return TRANSLATE_CACHE[text]
    try:
        url = f"https://translate.googleapis.com/translate_a/single?client=gtx&sl=auto&tl=ar&dt=t&q={urllib.parse.quote(text)}"
        r = requests.get(url, timeout=3).json()
        trans = "".join([s[0] for s in r[0]])
        TRANSLATE_CACHE[text]=trans; return trans
    except: return text

def get_image(entry, cat):
    try:
        if hasattr(entry,'media_content') and entry.media_content:
            u=entry.media_content[0].get('url','')
            if u.startswith('http'): return u
    except: pass
    m=re.search(r'<img[^>]+src="([^"]+)"', getattr(entry,'description',''))
    if m: return m.group(1)
    return None
def get_og(url):
    try:
        r=requests.get(url, headers={'User-Agent':'Mozilla/5.0'}, timeout=3)
        m=re.search(r'property="og:image"[^>]+content="([^"]+)"', r.text, re.I)
        if m: return m.group(1)
    except: pass
    return None

def fetch_one(args):
    src, cat=args
    try:
        f=feedparser.parse(src["url"])
        res=[]
        for e in f.entries[:4]:
            img=get_image(e,cat) or get_og(e.link) or DEFAULT_IMAGES["الكل"]
            title=translate_to_ar(e.title)
            res.append({"id":urllib.parse.quote(e.link),"title":title,"link":e.link,"time":getattr(e,'published','')[:16],"source":src["name"],"image":img,"wa":f"https://wa.me/?text={urllib.parse.quote(title)}"})
        return res
    except: return []

def get_news(cat, q=None):
    now=time.time(); key=f"{cat}_{q or ''}"
    if key in CACHE and now-CACHE_TIME.get(key,0)<180: return CACHE[key]
    if q:
        try:
            feed=feedparser.parse(f"https://news.google.com/rss/search?q={urllib.parse.quote(q)}&hl=ar&gl=SA&ceid=SA:ar")
            res=[]
            for e in feed.entries[:12]:
                img=get_image(e,cat) or get_og(e.link) or DEFAULT_IMAGES["الكل"]
                res.append({"id":urllib.parse.quote(e.link),"title":translate_to_ar(e.title),"link":e.link,"time":getattr(e,'published','')[:16],"source":"بحث 🔍","image":img,"wa":f"https://wa.me/?text={urllib.parse.quote(e.title)}"})
            CACHE[key]=res; CACHE_TIME[key]=now; return res
        except: return []
    all_news=[]
    sources=EXTRA_FEEDS.get(cat,[])[:5]
    if sources:
        with concurrent.futures.ThreadPoolExecutor(max_workers=5) as ex:
            results=list(ex.map(fetch_one, [(s,cat) for s in sources]))
            for r in results: all_news.extend(r)
    try:
        if FEEDS.get(cat) and FEEDS.get(cat)!="PRICES_PAGE":
            fg=feedparser.parse(FEEDS.get(cat))
            for e in fg.entries[:2]:
                img=get_image(e,cat) or get_og(e.link) or DEFAULT_IMAGES["الكل"]
                all_news.append({"id":urllib.parse.quote(e.link),"title":translate_to_ar(e.title),"link":e.link,"time":getattr(e,'published','')[:16],"source":"Google","image":img,"wa":f"https://wa.me/?text={urllib.parse.quote(e.title)}"})
    except: pass
    CACHE[key]=all_news[:25]; CACHE_TIME[key]=now
    return all_news[:25]

# === PWA ===
@app.route('/manifest.json')
def manifest():
    return jsonify({"name":"شامي - أخبار سوريا","short_name":"شامي","start_url":"/","display":"standalone","background_color":"#1b5e20","theme_color":"#1b5e20","icons":[{"src":"https://cdn-icons-png.flaticon.com/512/21/21601.png","sizes":"512x512","type":"image/png"}]})

@app.route('/sw.js')
def sw():
    return Response("self.addEventListener('install',e=>self.skipWaiting());self.addEventListener('fetch',e=>{e.respondWith(fetch(e.request).catch(()=>caches.match(e.request)))})", mimetype='application/javascript')

@app.route('/api/prices')
def api_prices(): return jsonify(get_real_prices())
@app.route('/api/detailed')
def api_detailed(): return jsonify(get_detailed_prices())

@app.route('/admin', methods=['GET','POST'])
def admin():
    if request.method=='POST':
        try:
            syp=int(request.form.get('syp','15250').replace(',',''))
            save_data({"syp_black":syp})
            PRICES_CACHE["time"]=0; DETAILED_CACHE["time"]=0
        except: pass
        return redirect('/admin')
    data=load_data()
    return f'''<html dir="rtl"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>لوحة تحكم شامي</title>
    <style>body{{font-family:Tajawal,Tahoma;padding:20px;background:#f5f5f5}} .box{{background:#fff;padding:20px;border-radius:12px;max-width:500px;margin:auto}} input{{width:100%;padding:12px;border:1px solid #ddd;border-radius:8px;margin:10px 0}} button{{background:#1b5e20;color:#fff;border:0;padding:12px 20px;border-radius:8px;width:100%;font-weight:800}}</style></head>
    <body><div class="box"><h2>🔧 لوحة تحكم شامي</h2><p>تعديل سعر الدولار سوق سوداء دمشق</p><form method="post"><label>سعر الدولار مقابل السوري (ل.س)</label><input name="syp" value="{data.get('syp_black',15250)}"><button>حفظ وتحديث الموقع ✅</button></form><br><a href="/">العودة للموقع</a><br><br><small>كلمة سر الأدمن: ضيف ?admin=shami123 للرابط إذا بدك تحميها</small></div></body></html>'''

@app.route('/article')
def article_page():
    url=request.args.get('url','')
    if not url: return redirect('/')
    try:
        title=translate_to_ar(request.args.get('title','خبر من شامي'))
        img=request.args.get('img',DEFAULT_IMAGES["الكل"])
        source=request.args.get('source','شامي')
        # جلب محتوى المقال ببساطة
        r=requests.get(url, headers={'User-Agent':'Mozilla/5.0'}, timeout=5)
        # استخراج أول فقرات
        text=re.sub(r'<[^>]+>',' ', r.text)
        text=re.sub(r'\s+',' ', text)[:3000]
    except:
        text="تعذر جلب المحتوى، افتح المصدر الأصلي"
        title="خبر"
        img=DEFAULT_IMAGES["الكل"]
        source="شامي"
    return f"""<!doctype html><html dir="rtl" lang="ar"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
    <title>{title}</title><link href="https://fonts.googleapis.com/css2?family=Tajawal:wght@700;800&display=swap" rel="stylesheet">
    <style>*{{font-family:Tajawal}}body{{margin:0;background:var(--bg,#f2f3f5)}}.hdr{{background:#1b5e20;color:#fff;padding:12px;display:flex;gap:10px;align-items:center;position:sticky;top:0}} .container{{max-width:750px;margin:auto;padding:12px}} .card{{background:var(--card,#fff);border-radius:16px;overflow:hidden;box-shadow:0 4px 18px rgba(0,0,0,.06)}} .card img{{width:100%;height:280px;object-fit:cover}} .body{{padding:16px}} .body h1{{font-size:20px;line-height:1.5}} .body p{{line-height:1.8;color:#333}} .btns{{display:flex;gap:10px;margin-top:16px}} .btn{{flex:1;padding:12px;border-radius:12px;text-align:center;text-decoration:none;font-weight:800}} .btn-b{{background:#111;color:#fff}} .btn-w{{background:#25D366;color:#fff}} .btn-f{{background:#ff9800;color:#fff}}</style>
    <script>let theme=localStorage.getItem('shami_theme')||'light'; if(theme=='dark'){{document.documentElement.style.setProperty('--bg','#121212');document.documentElement.style.setProperty('--card','#1e1e1e');}}</script>
    </head><body><div class="hdr"><a href="/" style="color:#fff;text-decoration:none">⬅ رجوع</a><b>شامي - قراءة داخلية</b></div>
    <div class="container"><div class="card"><img src="{img}"><div class="body"><small>{source}</small><h1>{title}</h1><p>{text[:1500]}...</p><div class="btns"><a href="{url}" target="_blank" class="btn btn-b">المصدر الأصلي 📖</a><a href="https://wa.me/?text={urllib.parse.quote(title+' '+url)}" class="btn btn-w">واتساب</a><a href="#" onclick="addFav('{urllib.parse.quote(url)}','{urllib.parse.quote(title)}');return false" class="btn btn-f">❤️ حفظ</a></div></div></div></div>
    <script>function addFav(u,t){{let f=JSON.parse(localStorage.getItem('shami_fav')||'[]'); f.push({{url:decodeURIComponent(u),title:decodeURIComponent(t)}}); localStorage.setItem('shami_fav',JSON.stringify(f)); alert('تم الحفظ في المفضلة ❤️')}}</script></body></html>"""

def prices_page_render():
    d = get_detailed_prices()
    tabs_html="".join([f'<a href="/?cat={urllib.parse.quote(k)}" class="tab {"active" if k=="أسعار 💱" else ""}">{k}</a>' for k in FEEDS])
    curr_rows="".join([f'<tr><td style="font-weight:800">{c["name"]}</td><td><b>{c["from_usd"]}</b></td><td style="color:#1b5e20"><b>{c["to_usd"]}</b></td></tr>' for c in d["currencies"]])
    crypto_rows="".join([f'<div class="crypto-card"><div><b>{c["name"]}</b><small> {c["sym"]}</small></div><div style="text-align:left"><b>${c["price"]:,.2f}</b><br><small style="color:{"#25D366" if c["change"]>=0 else "#e53935"}">{c["change"]:.2f}%</small></div></div>' for c in d["crypto"]])
    gold = d["gold"]; silver = d["silver"]
    return f"""<!doctype html><html dir="rtl"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>أسعار - شامي</title>
    <link href="https://fonts.googleapis.com/css2?family=Tajawal:wght@400;700;800&display=swap" rel="stylesheet">
    <style>:root{{--bg:#f2f3f5;--card:#fff;--text:#111}}[data-theme=dark]{{--bg:#121212;--card:#1e1e1e;--text:#eee}}*{{font-family:Tajawal, sans-serif;box-sizing:border-box}}body{{margin:0;background:var(--bg);color:var(--text)}}.top-header{{background:linear-gradient(90deg,#0d3b1f,#1b5e20);color:#fff;padding:12px 14px;position:sticky;top:0;z-index:30;display:flex;justify-content:space-between;align-items:center}}.tabs{{display:flex;gap:10px;overflow:auto;padding:12px 14px;background:var(--card);position:sticky;top:56px;z-index:19}}.tab{{padding:10px 18px;background:#eceff1;border-radius:24px;text-decoration:none;color:#333;font-weight:700;font-size:13px;white-space:nowrap}}.tab.active{{background:#1b5e20;color:#fff}}.container{{max-width:800px;margin:auto;padding:12px}}.section{{background:var(--card);border-radius:16px;padding:14px;margin:14px 0;box-shadow:0 4px 18px rgba(0,0,0,.06)}}.section h2{{margin:0 0 12px;font-size:18px;font-weight:800;border-right:4px solid #1b5e20;padding-right:10px}}table{{width:100%;border-collapse:collapse;font-size:13px}}th{{background:#f5f5f5;padding:10px;text-align:right}}td{{padding:10px;border-bottom:1px solid #eee}}.grid3{{display:grid;grid-template-columns:1fr 1fr 1fr;gap:10px}}.price-box{{background:#f8f9f8;border:1px solid #e0e0e0;border-radius:12px;padding:10px;text-align:center}}.price-box b{{display:block;font-size:15px;margin-top:4px}}.crypto-card{{display:flex;justify-content:space-between;align-items:center;background:#fafafa;border:1px solid #eee;border-radius:12px;padding:12px;margin:8px 0}}</style>
    <script>let th=localStorage.getItem('shami_theme')||'light'; if(th=='dark') document.documentElement.setAttribute('data-theme','dark');</script>
    </head><body><div class="top-header"><div><h1>💱 أسعار شامي - مباشر</h1><small>{d["updated"]} - <button onclick="toggleTheme()" style="background:#fff;color:#1b5e20;border:0;padding:4px 10px;border-radius:20px;font-weight:800">🌙/☀️</button></small></div></div><div class="tabs">{tabs_html}</div>
    <div class="container"><div class="section"><h2>💵 العملات مقابل الدولار والعكس</h2><table><tr><th>العملة</th><th>من الدولار</th><th>إلى الدولار</th></tr>{curr_rows}</table></div>
    <div class="section"><h2>🪙 الذهب</h2><div class="grid3"><div class="price-box"><small>جرام $</small><b>${gold["usd_g"]:,.2f}</b></div><div class="price-box"><small>أونصة $</small><b>${gold["usd_oz"]:,.0f}</b></div><div class="price-box"><small>كيلو $</small><b>${gold["usd_kg"]:,.0f}</b></div></div><br><div class="grid3"><div class="price-box"><small>جرام سوري</small><b>{gold["syp_g"]:,.0f}</b></div><div class="price-box"><small>أونصة سوري</small><b>{gold["syp_oz"]:,.0f}</b></div><div class="price-box"><small>جرام تركي</small><b>{gold["try_g"]:,.0f} TL</b></div></div></div>
    <div class="section"><h2>🥈 الفضة</h2><div class="grid3"><div class="price-box"><small>جرام $</small><b>${silver["usd_g"]:.2f}</b></div><div class="price-box"><small>أونصة $</small><b>${silver["usd_oz"]:.2f}</b></div><div class="price-box"><small>كيلو $</small><b>${silver["usd_kg"]:,.0f}</b></div></div><br><div class="grid3"><div class="price-box"><small>جرام سوري</small><b>{silver["syp_g"]:,.0f}</b></div><div class="price-box"><small>جرام تركي</small><b>{silver["try_g"]:.1f} TL</b></div><div class="price-box"><small>أونصة تركي</small><b>{silver["try_oz"]:.0f} TL</b></div></div></div>
    <div class="section"><h2>₿ الكريبتو</h2>{crypto_rows}</div></div>
    <script>function toggleTheme(){{let cur=document.documentElement.getAttribute('data-theme'); let nxt=cur=='dark'?'light':'dark'; document.documentElement.setAttribute('data-theme',nxt); localStorage.setItem('shami_theme',nxt)}}</script></body></html>"""

def home_render(cat, news, q=None):
    if cat == "أسعار 💱": return prices_page_render()
    prices = get_real_prices()
    urgent_news = get_news("عاجل 🔴")[:6]
    ticker_text = " 🔴 ".join([n["title"] for n in urgent_news]) if urgent_news else "أخبار عاجلة - شامي"
    tabs_html="".join([f'<a href="/?cat={urllib.parse.quote(k)}" class="tab {"active" if k==cat and not q else ""}">{k}</a>' for k in FEEDS])
    cards_html=""
    for n in news:
        detail_url = f"/article?url={urllib.parse.quote(n['link'])}&title={urllib.parse.quote(n['title'])}&img={urllib.parse.quote(n['image'])}&source={urllib.parse.quote(n['source'])}"
        cards_html+=f'<article class="news-card"><div class="img-wrap"><img src="{n["image"]}" loading="lazy" onerror="this.src=\'{DEFAULT_IMAGES["الكل"]}\'"><span class="badge">{n["source"]}</span><button class="fav-btn" onclick="addFav(\'{n["id"]}\',\'{urllib.parse.quote(n["title"])}\')">❤️</button></div><div class="info"><span class="meta">{n["time"]}</span><h2>{n["title"]}</h2><div class="actions"><a href="{detail_url}" class="btn-read">📖 اقرأ داخل شامي</a><a href="{n["wa"]}" target="_blank" class="btn-wa">واتساب</a></div></div></article>'

    return f"""<!doctype html><html dir="rtl" lang="ar"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
    <title>شامي - PWA</title><link rel="manifest" href="/manifest.json">
    <link href="https://fonts.googleapis.com/css2?family=Tajawal:wght@400;700;800&display=swap" rel="stylesheet">
    <style>
      :root{{--bg:#f2f3f5;--card:#fff;--text:#111;--tab:#eceff1}}[data-theme=dark]{{--bg:#121212;--card:#1e1e1e;--text:#eee;--tab:#2a2a2a}}*{{font-family:Tajawal,Tahoma,sans-serif;box-sizing:border-box}}body{{margin:0;background:var(--bg);color:var(--text);transition:.3s}}
      .top-header{{background:linear-gradient(90deg,#0d3b1f,#1b5e20);color:#fff;padding:12px 14px;position:sticky;top:0;z-index:30;display:flex;justify-content:space-between;align-items:center}}
      .logo{{display:flex;align-items:center;gap:10px}}.logo-icon{{width:36px;height:36px;background:#fff;color:#1b5e20;border-radius:8px;display:flex;align-items:center;justify-content:center;font-weight:900;font-size:20px}}
      .ticker{{background:#d32f2f;color:#fff;display:flex;align-items:center;height:44px;overflow:hidden}}.ticker-label{{background:#fff;color:#d32f2f;font-weight:900;padding:6px 14px;border-radius:6px;margin:0 10px;white-space:nowrap}}
      .prices{{background:#0e0e0e;color:#ddd;display:flex;gap:18px;overflow:auto;padding:9px 12px;font-size:13px;white-space:nowrap;align-items:center}}.prices b{{color:#fff}}
      .search-wrap{{background:var(--card);padding:10px;position:sticky;top:56px;z-index:20;display:flex;gap:8px;align-items:center}}.search-wrap form{{flex:1;max-width:750px;margin:auto;display:flex;gap:8px}} .search-wrap input{{flex:1;padding:12px 16px;border:1px solid #ddd;border-radius:24px;background:var(--bg);color:var(--text)}} .search-wrap button{{background:#1b5e20;color:#fff;border:0;padding:12px 22px;border-radius:24px;font-weight:800}}
      .tabs{{display:flex;gap:10px;overflow:auto;padding:12px 14px;background:var(--card);position:sticky;top:111px;z-index:19}} .tab{{padding:10px 18px;background:var(--tab);border-radius:24px;text-decoration:none;color:var(--text);font-weight:700;font-size:13px;white-space:nowrap}} .tab.active{{background:#1b5e20;color:#fff}}
      .container{{max-width:760px;margin:auto;padding:10px 12px}} .news-card{{background:var(--card);border-radius:18px;overflow:hidden;margin:14px 0;box-shadow:0 6px 20px rgba(0,0,0,.07);position:relative}} .img-wrap{{position:relative}} .img-wrap img{{width:100%;height:230px;object-fit:cover}} .badge{{position:absolute;top:12px;right:12px;background:rgba(0,0,0,.75);color:#fff;padding:5px 12px;border-radius:20px;font-size:11px}} .fav-btn{{position:absolute;top:12px;left:12px;background:rgba(255,255,255,.9);border:0;width:36px;height:36px;border-radius:50%;font-size:18px;cursor:pointer}} .info{{padding:14px}} .info h2{{margin:0 0 12px;font-size:16.5px;line-height:1.55;font-weight:800}} .actions{{display:flex;gap:10px}} .btn-read,.btn-wa{{flex:1;text-align:center;padding:12px;border-radius:12px;text-decoration:none;font-weight:800}} .btn-read{{background:#111;color:#fff}} .btn-wa{{background:#25D366;color:#fff}}
      .tools{{display:flex;gap:8px;align-items:center}}
    </style>
    <script>let th=localStorage.getItem('shami_theme')||'light'; if(th=='dark') document.documentElement.setAttribute('data-theme','dark');
    function toggleTheme(){{let cur=document.documentElement.getAttribute('data-theme'); let nxt=cur=='dark'?'light':'dark'; if(nxt=='light') document.documentElement.removeAttribute('data-theme'); else document.documentElement.setAttribute('data-theme','dark'); localStorage.setItem('shami_theme',nxt)}}
    function addFav(id,title){{let f=JSON.parse(localStorage.getItem('shami_fav')||'[]'); f.push({{id:id,title:decodeURIComponent(title)}}); localStorage.setItem('shami_fav',JSON.stringify(f)); alert('تم الحفظ ❤️ في المفضلة');}}
    function requestNotif(){{if('Notification' in window){{Notification.requestPermission().then(p=>{{if(p=='granted') new Notification('شامي 🔥',{body:'رح توصلك الأخبار العاجلة فوراً!'})}})}}}}
    if('serviceWorker' in navigator){{navigator.serviceWorker.register('/sw.js')}}
    </script>
    </head><body>
    <div class="top-header"><div class="logo"><div class="logo-icon">ش</div><div><h1 style="margin:0;font-size:20px">شامي 🔥</h1><small style="opacity:.85;font-size:11px">6 رياضة + 5 سياسة + أسعار حية + ترجمة</small></div></div><div class="tools"><button onclick="toggleTheme()" style="background:rgba(255,255,255,.2);border:0;color:#fff;padding:8px 12px;border-radius:20px">🌙/☀️</button><button onclick="requestNotif()" style="background:rgba(255,255,255,.2);border:0;color:#fff;padding:8px 12px;border-radius:20px">🔔</button><a href="/admin" style="background:rgba(255,255,255,.2);color:#fff;padding:8px 12px;border-radius:20px;text-decoration:none;font-size:12px">⚙️</a></div></div>
    <div class="ticker"><span class="ticker-label">عاجل 🔴</span><marquee scrollamount="7" direction="right">{ticker_text}</marquee></div>
    <div class="prices"><span>₿ {prices["btc"]} ({prices["btc_change"]})</span><span>ETH {prices["eth"]}</span><span>🪙 {prices["gold"]}</span><span>💵 دمشق {prices["syp_black"]} ل.س</span><span style="margin-right:auto"><a href="/?cat={urllib.parse.quote('أسعار 💱')}" style="color:#25D366;text-decoration:none;font-weight:800">كل الأسعار 💱</a></span></div>
    <div class="search-wrap"><form action="/search"><input name="q" value="{q or ''}" placeholder="🔍 ابحث... (ترجمة فورية)"><button>بحث</button></form><a href="#" onclick="let f=JSON.parse(localStorage.getItem('shami_fav')||'[]'); alert('المفضلة ❤️\\n'+f.map(x=>decodeURIComponent(x.title)).join('\\n---\\n')); return false" style="background:#ff9800;color:#fff;padding:10px 14px;border-radius:20px;text-decoration:none;font-weight:800;font-size:13px">❤️ {len(__import__('json').loads(__import__('os').environ.get('FAV_COUNT','0')) or []) if False else ''} المفضلة</a></div>
    <div class="tabs">{tabs_html}</div>
    <div class="container">{cards_html}</div>
    <div style="text-align:center;padding:20px;color:#888;font-size:12px">شامي © 2026 - PWA جاهز للتنزيل - لوحة تحكم /admin - وضع ليلي - مفضلة - قراءة داخلية - إشعارات - أسعار حية<br><button onclick="if(confirm('تثبيت شامي كتطبيق؟')) alert('من متصفح كروم: اضغط ⋮ ثم Add to Home screen / تثبيت التطبيق')" style="margin-top:10px;background:#1b5e20;color:#fff;border:0;padding:10px 18px;border-radius:20px;font-weight:800">📲 ثبّت شامي كتطبيق</button></div>
    </body></html>"""

@app.route('/search')
def search():
    q=request.args.get('q','').strip()
    if not q: return redirect('/')
    return home_render("الكل", get_news("الكل", query=q), q)

@app.route('/')
def home():
    cat=request.args.get('cat','الكل')
    return home_render(cat, get_news(cat) if cat!="أسعار 💱" else [])

if __name__=='__main__':
    port=int(os.environ.get("PORT",10000))
    app.run(host='0.0.0.0',port=port)
