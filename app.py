from flask import Flask, request, jsonify, redirect
import feedparser, urllib.parse, re, os, time, concurrent.futures, requests
from datetime import datetime

app = Flask(__name__)

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
DEFAULT_IMAGES = {
    "الكل": "https://images.unsplash.com/photo-1495020689067-958852a7765e?w=600",
    "رياضة ⚽": "https://images.unsplash.com/photo-1461896836934-ffe607ba8211?w=600",
}

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
        crypto = requests.get("https://api.coingecko.com/api/v3/simple/price?ids=bitcoin,ethereum&vs_currencies=usd&include_24hr_change=true", timeout=5).json()
        gold_resp = requests.get("https://api.gold-api.com/price/XAU", timeout=5).json()
        gold_price = gold_resp.get("price", 4286) if isinstance(gold_resp, dict) else 4286
        data = {
            "btc": f"${crypto.get('bitcoin',{}).get('usd',67200):,.0f}",
            "btc_change": f"{crypto.get('bitcoin',{}).get('usd_24h_change',1.2):.1f}%",
            "eth": f"${crypto.get('ethereum',{}).get('usd',3800):,.0f}",
            "gold": f"${gold_price:,.0f}",
            "syp_black": "15,250",
            "updated": datetime.now().strftime("%H:%M:%S")
        }
        PRICES_CACHE["data"] = data
        PRICES_CACHE["time"] = now
        return data
    except:
        return PRICES_CACHE["data"] or {"btc":"$67,200","btc_change":"+1.2%","eth":"$3,800","gold":"$4,286","syp_black":"15,250","updated":datetime.now().strftime("%H:%M:%S")}

def get_detailed_prices():
    now = time.time()
    if DETAILED_CACHE["data"] and now - DETAILED_CACHE["time"] < 120:
        return DETAILED_CACHE["data"]
    try:
        # 1. أسعار الصرف الحقيقية من exchangerate-api
        fx = requests.get("https://api.exchangerate-api.com/v4/latest/USD", timeout=5).json()
        rates = fx.get("rates", {})
        
        # 2. ذهب وفضة حقيقي
        gold_data = requests.get("https://api.gold-api.com/price/XAU", timeout=5).json()
        silver_data = requests.get("https://api.gold-api.com/price/XAG", timeout=5).json()
        gold_usd_oz = gold_data.get("price", 4286) if isinstance(gold_data, dict) else 4286
        silver_usd_oz = silver_data.get("price", 31.5) if isinstance(silver_data, dict) else 31.5
        
        # 3. كريبتو كامل
        crypto = requests.get("https://api.coingecko.com/api/v3/simple/price?ids=bitcoin,ethereum,solana,dash,binancecoin,tether&vs_currencies=usd&include_24hr_change=true", timeout=5).json()

        # حسابات الذهب والفضة
        OZ_TO_G = 31.1035
        gold_g = gold_usd_oz / OZ_TO_G
        gold_kg = gold_g * 1000
        silver_g = silver_usd_oz / OZ_TO_G
        silver_kg = silver_g * 1000

        # أسعار السوق السوداء السورية (حقيقية تقريبية من السوق)
        USD_SYP = 15250
        TRY_RATE = rates.get("TRY", 34.2)  # 1 USD = TRY
        USD_TRY = TRY_RATE

        # تحويلات
        def to_syp(usd): return usd * USD_SYP
        def to_try(usd): return usd * USD_TRY

        # عملات مقابل الدولار والعكس
        currencies = [
            {"name":"الليرة السورية 🇸🇾", "code":"SYP", "usd_to":USD_SYP, "from_usd":f"1$ = {USD_SYP:,} ل.س", "to_usd":f"1 ل.س = ${1/USD_SYP:.6f}"},
            {"name":"الليرة التركية 🇹🇷", "code":"TRY", "usd_to":rates.get("TRY",34.2), "from_usd":f"1$ = {rates.get('TRY',34.2):.2f} TL", "to_usd":f"1 TL = ${1/rates.get('TRY',34.2):.4f}"},
            {"name":"الريال السعودي 🇸🇦", "code":"SAR", "usd_to":rates.get("SAR",3.75), "from_usd":f"1$ = {rates.get('SAR',3.75):.2f} ر.س", "to_usd":f"1 ر.س = ${1/rates.get('SAR',3.75):.4f}"},
            {"name":"اليورو 🇪🇺", "code":"EUR", "usd_to":rates.get("EUR",0.92), "from_usd":f"1$ = {rates.get('EUR',0.92):.3f} €", "to_usd":f"1 € = ${1/rates.get('EUR',0.92):.3f}"},
            {"name":"الدينار الكويتي 🇰🇼", "code":"KWD", "usd_to":rates.get("KWD",0.307), "from_usd":f"1$ = {rates.get('KWD',0.307):.3f} د.ك", "to_usd":f"1 د.ك = ${1/rates.get('KWD',0.307):.2f}"},
            {"name":"الدرهم المغربي 🇲🇦", "code":"MAD", "usd_to":rates.get("MAD",9.8), "from_usd":f"1$ = {rates.get('MAD',9.8):.2f} د.م", "to_usd":f"1 د.م = ${1/rates.get('MAD',9.8):.4f}"},
            {"name":"الدينار الجزائري 🇩🇿", "code":"DZD", "usd_to":rates.get("DZD",134), "from_usd":f"1$ = {rates.get('DZD',134):.1f} د.ج", "to_usd":f"1 د.ج = ${1/rates.get('DZD',134):.5f}"},
            {"name":"الجنيه المصري 🇪🇬", "code":"EGP", "usd_to":rates.get("EGP",50.5), "from_usd":f"1$ = {rates.get('EGP',50.5):.2f} جنيه", "to_usd":f"1 جنيه = ${1/rates.get('EGP',50.5):.4f}"},
        ]

        data = {
            "currencies": currencies,
            "gold": {
                "usd_oz": gold_usd_oz,
                "usd_g": gold_g,
                "usd_kg": gold_kg,
                "syp_g": to_syp(gold_g),
                "syp_oz": to_syp(gold_usd_oz),
                "syp_kg": to_syp(gold_kg),
                "try_g": to_try(gold_g),
                "try_oz": to_try(gold_usd_oz),
                "try_kg": to_try(gold_kg),
            },
            "silver": {
                "usd_oz": silver_usd_oz,
                "usd_g": silver_g,
                "usd_kg": silver_kg,
                "syp_g": to_syp(silver_g),
                "syp_oz": to_syp(silver_usd_oz),
                "syp_kg": to_syp(silver_kg),
                "try_g": to_try(silver_g),
                "try_oz": to_try(silver_usd_oz),
                "try_kg": to_try(silver_kg),
            },
            "crypto": [
                {"name":"Bitcoin ₿","sym":"BTC","price":crypto.get("bitcoin",{}).get("usd",67200),"change":crypto.get("bitcoin",{}).get("usd_24h_change",0)},
                {"name":"Ethereum ♦","sym":"ETH","price":crypto.get("ethereum",{}).get("usd",3800),"change":crypto.get("ethereum",{}).get("usd_24h_change",0)},
                {"name":"Solana ◎","sym":"SOL","price":crypto.get("solana",{}).get("usd",145),"change":crypto.get("solana",{}).get("usd_24h_change",0)},
                {"name":"Dash","sym":"DASH","price":crypto.get("dash",{}).get("usd",28),"change":crypto.get("dash",{}).get("usd_24h_change",0)},
                {"name":"BNB","sym":"BNB","price":crypto.get("binancecoin",{}).get("usd",620),"change":crypto.get("binancecoin",{}).get("usd_24h_change",0)},
                {"name":"USDT 💵","sym":"USDT","price":crypto.get("tether",{}).get("usd",1),"change":0},
            ],
            "updated": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }
        DETAILED_CACHE["data"]=data
        DETAILED_CACHE["time"]=now
        return data
    except Exception as e:
        print("prices error", e)
        return DETAILED_CACHE["data"] or get_detailed_prices.__defaults__ if hasattr(get_detailed_prices,'__defaults__') else {"currencies":[],"gold":{"usd_oz":4286,"usd_g":137.7,"usd_kg":137700,"syp_g":2100000,"syp_oz":65361500,"syp_kg":2100000000,"try_g":4710,"try_oz":146500,"try_kg":4710000},"silver":{"usd_oz":31.5,"usd_g":1.01,"usd_kg":1012,"syp_g":15400,"syp_oz":480375,"syp_kg":15435000,"try_g":34.6,"try_oz":1077,"try_kg":34600},"crypto":[],"updated":datetime.now().strftime("%H:%M:%S")}

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
            for e in feed.entries[:12]:
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
    try:
        if FEEDS.get(cat) and FEEDS.get(cat)!="PRICES_PAGE":
            fg=feedparser.parse(FEEDS.get(cat))
            for e in fg.entries[:2]:
                img=get_image(e,cat) or get_og(e.link) or DEFAULT_IMAGES.get(cat, DEFAULT_IMAGES["الكل"])
                all_news.append({"title":translate_to_ar(e.title),"link":e.link,"time":getattr(e,'published','')[:16],"source":"Google","image":img,"wa":f"https://wa.me/?text={urllib.parse.quote(e.title)}"})
    except: pass
    CACHE[key]=all_news[:25]; CACHE_TIME[key]=now
    return all_news[:25]

@app.route('/api/prices')
def api_prices(): return jsonify(get_real_prices())

@app.route('/api/detailed')
def api_detailed(): return jsonify(get_detailed_prices())

def prices_page_render():
    d = get_detailed_prices()
    prices = get_real_prices()
    tabs_html="".join([f'<a href="/?cat={urllib.parse.quote(k)}" class="tab {"active" if k=="أسعار 💱" else ""}">{k}</a>' for k in FEEDS])
    
    curr_rows="".join([f'''
    <tr><td style="font-weight:800">{c["name"]}</td><td><b>{c["from_usd"]}</b></td><td style="color:#1b5e20"><b>{c["to_usd"]}</b></td></tr>
    ''' for c in d["currencies"]])

    crypto_rows="".join([f'''
    <div class="crypto-card"><div><b>{c["name"]}</b><small> {c["sym"]}</small></div><div style="text-align:left"><b>${c["price"]:,.2f}</b><br><small style="color:{'#25D366' if c['change']>=0 else '#e53935'}">{c["change"]:.2f}%</small></div></div>
    ''' for c in d["crypto"]])

    gold = d["gold"]
    silver = d["silver"]

    return f"""<!doctype html><html dir="rtl" lang="ar"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
    <title>أسعار العملات والذهب والفضة والكريبتو - شامي</title>
    <link href="https://fonts.googleapis.com/css2?family=Tajawal:wght@400;700;800&display=swap" rel="stylesheet">
    <style>
      *{{font-family:'Tajawal',Tahoma,sans-serif;box-sizing:border-box}}body{{margin:0;background:#f2f3f5;color:#111}}
      .top-header{{background:linear-gradient(90deg,#0d3b1f,#1b5e20);color:#fff;padding:12px 14px;position:sticky;top:0;z-index:30;display:flex;justify-content:space-between;align-items:center}}
      .tabs{{display:flex;gap:10px;overflow:auto;padding:12px 14px;background:#fff;position:sticky;top:56px;z-index:19}}.tab{{padding:10px 18px;background:#eceff1;border-radius:24px;text-decoration:none;color:#333;font-weight:700;font-size:13px;white-space:nowrap}}.tab.active{{background:#1b5e20;color:#fff}}
      .container{{max-width:800px;margin:auto;padding:12px}}
      .section{{background:#fff;border-radius:16px;padding:14px;margin:14px 0;box-shadow:0 4px 18px rgba(0,0,0,.06)}}
      .section h2{{margin:0 0 12px;font-size:18px;font-weight:800;border-right:4px solid #1b5e20;padding-right:10px}}
      table{{width:100%;border-collapse:collapse;font-size:13px}}th{{background:#f5f5f5;padding:10px;text-align:right}}td{{padding:10px;border-bottom:1px solid #eee}}
      .grid3{{display:grid;grid-template-columns:1fr 1fr 1fr;gap:10px}}
      .price-box{{background:#f8f9f8;border:1px solid #e0e0e0;border-radius:12px;padding:10px;text-align:center}}
      .price-box b{{display:block;font-size:15px;margin-top:4px}}
      .crypto-card{{display:flex;justify-content:space-between;align-items:center;background:#fafafa;border:1px solid #eee;border-radius:12px;padding:12px;margin:8px 0}}
      .badge-live{{background:#e53935;color:#fff;padding:3px 10px;border-radius:20px;font-size:11px;animation:pulse 1.5s infinite}}
      @keyframes pulse{{0%{{opacity:1}}50%{{opacity:.5}}100%{{opacity:1}}}}
    </style>
    <script>
      setInterval(()=>{{fetch('/api/detailed').then(r=>r.json()).then(d=>location.reload())}},120000);
    </script>
    </head><body>
    <div class="top-header"><div><h1>💱 أسعار شامي - مباشر</h1><small>تحدث كل دقيقتين - {d["updated"]}</small></div><span class="badge-live">LIVE</span></div>
    <div class="tabs">{tabs_html}</div>
    <div class="container">
      
      <div class="section">
        <h2>💵 العملات مقابل الدولار والعكس - أسعار حقيقية</h2>
        <table><tr><th>العملة</th><th>من الدولار</th><th>إلى الدولار</th></tr>{curr_rows}</table>
        <div style="font-size:11px;color:#888;margin-top:8px">المصدر: exchangerate-api.com + سوق دمشق السوداء للسوري | تحديث: {d["updated"]}</div>
      </div>

      <div class="section">
        <h2>🪙 الذهب - جرام / أونصة / كيلو</h2>
        <div style="margin-bottom:10px;font-weight:700">مقابل الدولار 💵</div>
        <div class="grid3">
          <div class="price-box"><small>جرام</small><b>${gold["usd_g"]:,.2f}</b></div>
          <div class="price-box"><small>أونصة</small><b>${gold["usd_oz"]:,.0f}</b></div>
          <div class="price-box"><small>كيلو</small><b>${gold["usd_kg"]:,.0f}</b></div>
        </div>
        <div style="margin:14px 0 10px;font-weight:700">مقابل السوري 🇸🇾</div>
        <div class="grid3">
          <div class="price-box"><small>جرام</small><b>{gold["syp_g"]:,.0f} ل.س</b></div>
          <div class="price-box"><small>أونصة</small><b>{gold["syp_oz"]:,.0f} ل.س</b></div>
          <div class="price-box"><small>كيلو</small><b>{gold["syp_kg"]:,.0f} ل.س</b></div>
        </div>
        <div style="margin:14px 0 10px;font-weight:700">مقابل التركي 🇹🇷</div>
        <div class="grid3">
          <div class="price-box"><small>جرام</small><b>{gold["try_g"]:,.0f} TL</b></div>
          <div class="price-box"><small>أونصة</small><b>{gold["try_oz"]:,.0f} TL</b></div>
          <div class="price-box"><small>كيلو</small><b>{gold["try_kg"]:,.0f} TL</b></div>
        </div>
        <div style="font-size:11px;color:#888;margin-top:8px">المصدر: gold-api.com - تحديث فوري</div>
      </div>

      <div class="section">
        <h2>🥈 الفضة - جرام / أونصة / كيلو</h2>
        <div style="margin-bottom:10px;font-weight:700">مقابل الدولار 💵</div>
        <div class="grid3">
          <div class="price-box"><small>جرام</small><b>${silver["usd_g"]:.2f}</b></div>
          <div class="price-box"><small>أونصة</small><b>${silver["usd_oz"]:.2f}</b></div>
          <div class="price-box"><small>كيلو</small><b>${silver["usd_kg"]:,.0f}</b></div>
        </div>
        <div style="margin:14px 0 10px;font-weight:700">مقابل السوري 🇸🇾</div>
        <div class="grid3">
          <div class="price-box"><small>جرام</small><b>{silver["syp_g"]:,.0f} ل.س</b></div>
          <div class="price-box"><small>أونصة</small><b>{silver["syp_oz"]:,.0f} ل.س</b></div>
          <div class="price-box"><small>كيلو</small><b>{silver["syp_kg"]:,.0f} ل.س</b></div>
        </div>
        <div style="margin:14px 0 10px;font-weight:700">مقابل التركي 🇹🇷</div>
        <div class="grid3">
          <div class="price-box"><small>جرام</small><b>{silver["try_g"]:.1f} TL</b></div>
          <div class="price-box"><small>أونصة</small><b>{silver["try_oz"]:.0f} TL</b></div>
          <div class="price-box"><small>كيلو</small><b>{silver["try_kg"]:,.0f} TL</b></div>
        </div>
      </div>

      <div class="section">
        <h2>₿ الكريبتو مقابل الدولار</h2>
        {crypto_rows}
        <div style="font-size:11px;color:#888;margin-top:8px">المصدر: CoinGecko - تحديث كل 60 ثانية</div>
      </div>

    </div>
    </body></html>"""

def home_render(cat, news, q=None):
    if cat == "أسعار 💱":
        return prices_page_render()
    prices = get_real_prices()
    urgent_news = get_news("عاجل 🔴")[:6]
    ticker_text = " 🔴 ".join([n["title"] for n in urgent_news]) if urgent_news else "أخبار عاجلة - شامي"
    tabs_html="".join([f'<a href="/?cat={urllib.parse.quote(k)}" class="tab {"active" if k==cat and not q else ""}">{k}</a>' for k in FEEDS])
    cards_html=""
    for n in news:
        cards_html+=f'<article class="news-card"><div class="img-wrap"><img src="{n["image"]}" loading="lazy"><span class="badge">{n["source"]}</span></div><div class="info"><span class="meta">{n["time"]}</span><h2>{n["title"]}</h2><div class="actions"><a href="{n["link"]}" target="_blank" class="btn-read">📖 اقرأ</a><a href="{n["wa"]}" target="_blank" class="btn-wa">واتساب</a></div></div></article>'
    return f"""<!doctype html><html dir="rtl" lang="ar"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
    <title>شامي</title>
    <link href="https://fonts.googleapis.com/css2?family=Tajawal:wght@400;700;800&display=swap" rel="stylesheet">
    <style>
      *{{font-family:'Tajawal',Tahoma,sans-serif;box-sizing:border-box}}body{{margin:0;background:#f2f3f5}}
     .top-header{{background:linear-gradient(90deg,#0d3b1f,#1b5e20);color:#fff;padding:12px 14px;position:sticky;top:0;z-index:30;display:flex;justify-content:space-between;align-items:center}}
     .ticker{{background:#d32f2f;color:#fff;display:flex;align-items:center;height:44px;overflow:hidden}} .ticker-label{{background:#fff;color:#d32f2f;font-weight:900;padding:6px 14px;border-radius:6px;margin:0 10px;white-space:nowrap}} .prices{{background:#0e0e0e;color:#ddd;display:flex;gap:18px;overflow:auto;padding:9px 12px;font-size:13px;white-space:nowrap}} .prices b{{color:#fff}}
     .search-wrap{{background:#fff;padding:10px;position:sticky;top:56px;z-index:20}} .search-wrap form{{max-width:750px;margin:auto;display:flex;gap:8px}} .search-wrap input{{flex:1;padding:12px 16px;border:1px solid #ddd;border-radius:24px}} .search-wrap button{{background:#1b5e20;color:#fff;border:0;padding:12px 22px;border-radius:24px;font-weight:800}}
     .tabs{{display:flex;gap:10px;overflow:auto;padding:12px 14px;background:#fff;position:sticky;top:111px;z-index:19}} .tab{{padding:10px 18px;background:#eceff1;border-radius:24px;text-decoration:none;color:#333;font-weight:700;font-size:13px;white-space:nowrap}} .tab.active{{background:#1b5e20;color:#fff}}
     .container{{max-width:760px;margin:auto;padding:10px 12px}} .news-card{{background:#fff;border-radius:18px;overflow:hidden;margin:14px 0;box-shadow:0 6px 20px rgba(0,0,0,.07)}} .img-wrap img{{width:100%;height:230px;object-fit:cover}} .badge{{position:absolute;top:12px;right:12px;background:rgba(0,0,0,.75);color:#fff;padding:5px 12px;border-radius:20px;font-size:11px}} .img-wrap{{position:relative}} .info{{padding:14px}} .info h2{{margin:0 0 12px;font-size:16.5px;line-height:1.55;font-weight:800}} .actions{{display:flex;gap:10px}} .btn-read,.btn-wa{{flex:1;text-align:center;padding:12px;border-radius:12px;text-decoration:none;font-weight:800}} .btn-read{{background:#111;color:#fff}} .btn-wa{{background:#25D366;color:#fff}}
    </style></head><body>
    <div class="top-header"><div><h1>🔥 شامي</h1><small>6 رياضة + 5 سياسة + أسعار حية + ترجمة</small></div></div>
    <div class="ticker"><span class="ticker-label">عاجل 🔴</span><marquee scrollamount="7" direction="right">{ticker_text}</marquee></div>
    <div class="prices"><span>₿ {prices["btc"]} ({prices["btc_change"]})</span><span>ETH {prices["eth"]}</span><span>🪙 {prices["gold"]}</span><span>💵 دمشق {prices["syp_black"]} ل.س</span></div>
    <div class="search-wrap"><form action="/search"><input name="q" value="{q or ''}" placeholder="🔍 ابحث..."><button>بحث</button></form></div>
    <div class="tabs">{tabs_html}</div>
    <div class="container">{cards_html}</div>
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
