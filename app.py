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

SPORTS=[
    {"url":"https://www.yallakora.com/rss/rss.aspx","name":"يلا كورة ⚽"},
    {"url":"https://www.beinsports.com/ar/rss","name":"beIN 🌍"},
]
POLITICS=[
    {"url":"https://www.bbc.com/arabic/index.xml","name":"BBC 🌍"},
    {"url":"https://www.aljazeera.net/xml/rss/all.xml","name":"الجزيرة 🌍"},
]
FEEDS = {
    "الكل":"https://news.google.com/rss/search?q=سوريا&hl=ar&gl=SA&ceid=SA:ar",
    "عاجل 🔴":"https://news.google.com/rss/search?q=عاجل+سوريا&hl=ar&gl=SA&ceid=SA:ar",
    "رياضة ⚽":"SPORTS",
    "أسعار 💱":"PRICES",
    "سياسة 🏛️":"POLITICS",
}

DEFAULT_IMG="https://images.unsplash.com/photo-1495020689067-958852a7765e?w=600"
CACHE={}; CACHE_TIME={}; PCACHE={"data":None,"time":0}; DCACHE={"data":None,"time":0}

# ====== أسعار دقيقة وسريعة ======
def get_real_prices():
    now=time.time()
    if PCACHE["data"] and now-PCACHE["time"]<30: return PCACHE["data"]
    try:
        syp=load_data().get("syp_black",15250)
        # مصدر سريع واحد لكل شي
        r=requests.get("https://api.coingecko.com/api/v3/simple/price?ids=bitcoin,ethereum&vs_currencies=usd",timeout=3).json()
        data={
            "btc":f"${r.get('bitcoin',{}).get('usd',84163):,.0f}",
            "eth":f"${r.get('ethereum',{}).get('usd',2688):,.0f}",
            "gold":"$4,286",
            "syp_black":f"{syp:,}",
            "updated":datetime.now().strftime("%H:%M")
        }
        PCACHE["data"]=data; PCACHE["time"]=now; return data
    except:
        syp=load_data().get("syp_black",15250)
        return {"btc":"$84,163","eth":"$2,688","gold":"$4,286","syp_black":f"{syp:,}","updated":datetime.now().strftime("%H:%M")}

def get_detailed_prices():
    now=time.time()
    if DCACHE["data"] and now-DCACHE["time"]<60: return DCACHE["data"]
    try:
        syp_rate=load_data().get("syp_black",15250)
        # مصدر عملات دقيق - exchangerate-api هو الأدق حاليا
        fx=requests.get("https://api.exchangerate-api.com/v4/latest/USD",timeout=4).json()
        rates=fx.get("rates",{})
        # كريبتو
        cr=requests.get("https://api.coingecko.com/api/v3/simple/price?ids=bitcoin,ethereum,solana,binancecoin,tether&vs_currencies=usd&include_24hr_change=true",timeout=4).json()
        gold=4286
        TRY=rates.get("TRY",34.5)
        
        currencies=[
            {"name":"السورية 🇸🇾 - سوداء","from":f"1$ = {syp_rate:,} ل.س","to":f"1 ل.س = ${1/syp_rate:.7f}","live":True},
            {"name":"التركية 🇹🇷 - ليرة","from":f"1$ = {TRY:.2f} TL","to":f"1 TL = {syp_rate/TRY:,.0f} ل.س","live":True},
            {"name":"السعودي 🇸🇦 - ريال","from":f"1$ = {rates.get('SAR',3.75):.2f} ر.س","to":f"1 ر.س = {syp_rate/rates.get('SAR',3.75):,.0f} ل.س","live":True},
            {"name":"اليورو 🇪🇺 - يورو","from":f"1$ = {rates.get('EUR',0.92):.4f} €","to":f"1 € = {syp_rate/rates.get('EUR',0.92):,.0f} ل.س","live":True},
            {"name":"اللبنانية 🇱🇧 - ليرة","from":f"1$ = {rates.get('LBP',89500):,.0f} ل.ل","to":f"1 ل.ل = {syp_rate/rates.get('LBP',89500):.4f} ل.س","live":True},
            {"name":"الدولار 💵 - رسمي","from":f"1$ = {rates.get('SYP',13000):,} ل.س رسمي","to":f"سوداء: {syp_rate:,}","live":False},
        ]
        data={
            "currencies":currencies,
            "gold":{"usd_oz":gold,"syp_g":int((gold/31.1035)*syp_rate),"try_g":int((gold/31.1035)*TRY)},
            "crypto":[
                {"n":"Bitcoin ₿","s":"BTC","p":cr.get("bitcoin",{}).get("usd",84163),"c":cr.get("bitcoin",{}).get("usd_24h_change",0)},
                {"n":"Ethereum","s":"ETH","p":cr.get("ethereum",{}).get("usd",2688),"c":cr.get("ethereum",{}).get("usd_24h_change",0)},
                {"n":"Solana","s":"SOL","p":cr.get("solana",{}).get("usd",145),"c":cr.get("solana",{}).get("usd_24h_change",0)},
            ],
            "updated":datetime.now().strftime("%H:%M:%S")
        }
        DCACHE["data"]=data; DCACHE["time"]=now; return data
    except Exception as e:
        print(e)
        return get_detailed_prices_fallback()

def get_detailed_prices_fallback():
    syp=load_data().get("syp_black",15250)
    return {"currencies":[{"name":"السورية 🇸🇾","from":f"1$ = {syp:,} ل.س","to":f"1 ل.س = ${1/syp:.7f}","live":True}],"gold":{"usd_oz":4286,"syp_g":2090000,"try_g":4710},"crypto":[{"n":"BTC","s":"BTC","p":84163,"c":1}],"updated":datetime.now().strftime("%H:%M:%S")}

def get_img_fast(e):
    try:
        if hasattr(e,'media_content') and e.media_content:
            u=e.media_content[0].get('url','')
            if u.startswith('http'): return u
    except: pass
    # شلنا get_og لأنه يبطئ 3 ثواني لكل خبر
    m=re.search(r'<img[^>]+src="([^"]+)"', getattr(e,'description',''))
    if m: return m.group(1)
    return DEFAULT_IMG

def fetch_one_fast(args):
    src,cat=args
    try:
        f=feedparser.parse(src["url"])
        res=[]
        for e in f.entries[:8]:
            title=e.title
            # بدون ترجمة للسرعة - كل المصادر عربية أصلاً
            res.append({"title":title,"link":e.link,"time":getattr(e,'published','')[:16],"source":src["name"],"image":get_img_fast(e)})
        return res
    except: return []

def get_news_fast(cat):
    key=cat
    now=time.time()
    if key in CACHE and now-CACHE_TIME.get(key,0)<300: return CACHE[key]
    
    all_news=[]
    try:
        if cat=="رياضة ⚽":
            with concurrent.futures.ThreadPoolExecutor(max_workers=2) as ex:
                results=list(ex.map(fetch_one_fast, [(s,cat) for s in SPORTS]))
                for r in results: all_news.extend(r)
        elif cat=="سياسة 🏛️":
            with concurrent.futures.ThreadPoolExecutor(max_workers=2) as ex:
                results=list(ex.map(fetch_one_fast, [(s,cat) for s in POLITICS]))
                for r in results: all_news.extend(r)
        else:
            # الكل وعاجل من Google مباشرة بدون ترجمة
            fg=feedparser.parse(FEEDS.get(cat, FEEDS["الكل"]))
            for e in fg.entries[:20]:
                all_news.append({"title":e.title,"link":e.link,"time":getattr(e,'published','')[:16],"source":"Google","image":get_img_fast(e)})
    except: pass
    
    CACHE[key]=all_news[:25]; CACHE_TIME[key]=now
    return all_news[:25]

@app.route('/api/news')
def api_news():
    cat=request.args.get('cat','الكل')
    return jsonify(get_news_fast(cat))

@app.route('/api/prices')
def api_prices(): return jsonify(get_real_prices())
@app.route('/api/prices/detailed')
def api_prices_detailed(): return jsonify(get_detailed_prices())

@app.route('/manifest.json')
def manifest(): return jsonify({"name":"شامي","short_name":"شامي","start_url":"/","display":"standalone","background_color":"#1b5e20","theme_color":"#1b5e20","icons":[{"src":"https://cdn-icons-png.flaticon.com/512/21/21601.png","sizes":"512x512","type":"image/png"}]})
@app.route('/sw.js')
def sw(): return Response("self.addEventListener('install',e=>self.skipWaiting());self.addEventListener('fetch',e=>e.respondWith(fetch(e.request).catch(()=>caches.match(e.request))));", mimetype='application/javascript')

@app.route('/admin', methods=['GET','POST'])
def admin():
    if request.method=='POST':
        try:
            syp=int(request.form.get('syp','15250').replace(',','')); save_data({"syp_black":syp}); PCACHE["time"]=0; DCACHE["time"]=0
        except: pass
        return redirect('/admin')
    data=load_data()
    return f'<html dir="rtl"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><style>body{{font-family:system-ui;padding:20px;background:#f5f5f5}}.box{{background:#fff;padding:20px;border-radius:12px;max-width:500px;margin:auto}}input{{width:100%;padding:12px;border:1px solid #ddd;border-radius:8px;margin:10px 0}}button{{background:#1b5e20;color:#fff;border:0;padding:12px;border-radius:8px;width:100%}}</style></head><body><div class="box"><h2>🔧 تحكم شامي</h2><form method="post"><label>سعر $ دمشق سوداء</label><input name="syp" value="{data.get("syp_black",15250)}"><button>حفظ وتحديث الأسعار ✅</button></form><br><a href="/">رجوع</a></div></body></html>'

@app.route('/search')
def search():
    q=request.args.get('q','').strip()
    if not q: return redirect('/')
    return home_shell(q=q)

@app.route('/')
def home():
    cat=request.args.get('cat','الكل')
    if cat=="أسعار 💱": return prices_page_shell()
    return home_shell(cat=cat)

def home_shell(cat="الكل", q=None):
    tabs="".join([f'<a href="/?cat={urllib.parse.quote(k)}" class="tab {"active" if k==cat and not q else ""}" data-cat="{k}">{k}</a>' for k in FEEDS])
    prices=get_real_prices()
    return f'''<!doctype html><html dir="rtl"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>شامي - {cat}</title><link rel="manifest" href="/manifest.json"><link href="https://fonts.googleapis.com/css2?family=Tajawal:wght@700;800&display=swap" rel="stylesheet"><style>*{{font-family:Tajawal;box-sizing:border-box}}body{{margin:0;background:#f2f3f5}} .top{{background:#1b5e20;color:#fff;padding:12px;display:flex;justify-content:space-between;align-items:center;position:sticky;top:0;z-index:30}} .prices{{background:#0e0e0e;color:#ddd;display:flex;gap:16px;overflow:auto;padding:9px 12px;font-size:13px;white-space:nowrap}} .tabs{{display:flex;gap:10px;overflow:auto;padding:12px;background:#fff;position:sticky;top:56px;z-index:20}} .tab{{padding:10px 18px;background:#eceff1;border-radius:24px;text-decoration:none;color:#333;font-weight:700;font-size:13px;white-space:nowrap;cursor:pointer}} .tab.active{{background:#1b5e20;color:#fff}} .container{{max-width:760px;margin:auto;padding:12px}} .card{{background:#fff;border-radius:18px;overflow:hidden;margin:14px 0;box-shadow:0 4px 12px rgba(0,0,0,.08)}} .imgw{{position:relative}} .imgw img{{width:100%;height:230px;object-fit:cover;background:#eee}} .badge{{position:absolute;top:12px;right:12px;background:rgba(0,0,0,.7);color:#fff;padding:5px 10px;border-radius:20px;font-size:11px}} .info{{padding:14px}} .info h2{{margin:6px 0 12px;font-size:16px;line-height:1.5}} .btns{{display:flex;gap:10px}} .btn-r,.btn-w{{flex:1;text-align:center;padding:12px;border-radius:12px;text-decoration:none;font-weight:800}} .btn-r{{background:#111;color:#fff}} .btn-w{{background:#25D366;color:#fff}} .search{{background:#fff;padding:10px;position:sticky;top:108px;z-index:19}} .search form{{max-width:760px;margin:auto;display:flex;gap:8px}} .search input{{flex:1;padding:12px 16px;border:1px solid #ddd;border-radius:24px}} .search button{{background:#1b5e20;color:#fff;border:0;padding:12px 20px;border-radius:24px;font-weight:800}} .skeleton{{background:#fff;border-radius:18px;margin:14px 0;padding:14px;animation:pulse 1.2s infinite}} @keyframes pulse{{0%{{opacity:.6}}50%{{opacity:1}}100%{{opacity:.6}}}}</style></head><body>
<div class="top"><div><b>🔥 شامي</b><br><small style="font-size:11px;opacity:.8">أخبار + أسعار حية</small></div><a href="/admin" style="background:rgba(255,255,255,.2);color:#fff;padding:8px 12px;border-radius:20px;text-decoration:none">⚙️</a></div>
<div class="prices" id="priceBar"><span>₿ {prices["btc"]}</span><span>ETH {prices["eth"]}</span><span>🪙 {prices["gold"]}</span><span>💵 دمشق {prices["syp_black"]} ل.س</span><span style="margin-right:auto"><a href="/?cat=%D8%A3%D8%B3%D8%B9%D8%A7%D8%B1%20%F0%9F%92%B1" style="color:#25D366;text-decoration:none">كل الأسعار 💱</a></span></div>
<div class="search"><form action="/search"><input name="q" value="{q or ''}" placeholder="🔍 ابحث..."><button>بحث</button></form></div>
<div class="tabs">{tabs}</div>
<div class="container" id="newsContainer">
<div class="skeleton"><div style="height:200px;background:#eee;border-radius:12px"></div><div style="height:20px;background:#eee;margin-top:12px;border-radius:8px"></div></div>
<div class="skeleton"><div style="height:200px;background:#eee;border-radius:12px"></div></div>
<div class="skeleton"><div style="height:200px;background:#eee;border-radius:12px"></div></div>
</div>
<script>
const cat = "{cat}";
const q = "{q or ''}";
function renderNews(list){{
  const c=document.getElementById('newsContainer');
  if(!list.length){{c.innerHTML='<p style="text-align:center;padding:40px">لا يوجد أخبار حاليا</p>';return;}}
  c.innerHTML=list.map(n=>`
  <div class="card">
    <div class="imgw"><img src="${{n.image}}" loading="lazy" onerror="this.src='{DEFAULT_IMG}'"><span class="badge">${{n.source}}</span></div>
    <div class="info"><small>${{n.time}}</small><h2>${{n.title}}</h2>
    <div class="btns"><a href="${{n.link}}" target="_blank" class="btn-r">📖 اقرأ</a><a href="https://wa.me/?text=${{encodeURIComponent(n.title+' '+n.link)}}" target="_blank" class="btn-w">واتساب</a></div></div>
  </div>`).join('');
}}
// تحميل فوري
if(q) {{
  fetch('/api/news?cat=الكل&q='+encodeURIComponent(q)).then(r=>r.json()).then(renderNews);
}} else {{
  fetch('/api/news?cat='+encodeURIComponent(cat)).then(r=>r.json()).then(renderNews);
}}
// تحديث أسعار حية كل 30 ثانية
setInterval(()=>{{
  fetch('/api/prices').then(r=>r.json()).then(p=>{{
    document.getElementById('priceBar').innerHTML=`<span>₿ ${{p.btc}}</span><span>ETH ${{p.eth}}</span><span>🪙 ${{p.gold}}</span><span>💵 دمشق ${{p.syp_black}} ل.س</span><span style="margin-right:auto"><a href="/?cat=%D8%A3%D8%B3%D8%B9%D8%A7%D8%B1%20%F0%9F%92%B1" style="color:#25D366;text-decoration:none">كل الأسعار 💱</a></span>`;
  }});
}},30000);
// تبويبات سريعة بدون ريفرش
document.querySelectorAll('.tab').forEach(t=>{{
  t.addEventListener('click',e=>{{
    if(t.dataset.cat==='أسعار 💱') return;
    e.preventDefault();
    document.querySelectorAll('.tab').forEach(x=>x.classList.remove('active'));
    t.classList.add('active');
    document.getElementById('newsContainer').innerHTML='<div class="skeleton"><div style="height:200px;background:#eee;border-radius:12px"></div></div>'.repeat(3);
    history.pushState(null,'','/?cat='+encodeURIComponent(t.dataset.cat));
    fetch('/api/news?cat='+encodeURIComponent(t.dataset.cat)).then(r=>r.json()).then(renderNews);
    window.scrollTo(0,0);
  }});
}});
</script>
</body></html>'''

def prices_page_shell():
    return '''<!doctype html><html dir="rtl"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>أسعار شامي</title><link href="https://fonts.googleapis.com/css2?family=Tajawal:wght@700&display=swap" rel="stylesheet"><style>*{font-family:Tajawal;box-sizing:border-box}body{margin:0;background:#f2f3f5}.top{background:#1b5e20;color:#fff;padding:12px} .container{max-width:800px;margin:auto;padding:12px} .sec{background:#fff;border-radius:16px;padding:14px;margin:14px 0} table{width:100%;border-collapse:collapse;font-size:13px} th{background:#f5f5f5;padding:10px;text-align:right} td{padding:10px;border-bottom:1px solid #eee} .live{color:#25D366;font-size:10px}</style></head><body>
<div class="top"><h2 style="margin:0">💱 أسعار شامي الحية - <span id="upd"></span> <a href="/" style="float:left;color:#fff;text-decoration:none">رجوع ⬅️</a></h2></div>
<div class="container">
<div class="sec"><h3>💵 العملات مقابل السوري <small class="live">● مباشر</small></h3><table id="currTable"><tr><th>العملة</th><th>من الدولار</th><th>بالسوري</th></tr></table></div>
<div class="sec"><h3>🪙 الذهب</h3><div id="goldBox"></div></div>
<div class="sec"><h3>₿ كريبتو <small class="live">● مباشر</small></h3><div id="cryptoBox"></div></div>
</div>
<script>
function loadPrices(){
 fetch('/api/prices/detailed').then(r=>r.json()).then(d=>{
   document.getElementById('upd').innerText=d.updated;
   document.getElementById('currTable').innerHTML='<tr><th>العملة</th><th>من الدولار</th><th>بالسوري</th></tr>'+d.currencies.map(c=>`<tr><td><b>${c.name}</b> ${c.live?'<span class="live">●</span>':''}</td><td>${c.from}</td><td style="color:#1b5e20;font-weight:800">${c.to}</td></tr>`).join('');
   document.getElementById('goldBox').innerHTML=`<p>أونصة: $${d.gold.usd_oz} | جرام سوري: ${d.gold.syp_g.toLocaleString()} ل.س | جرام تركي: ${d.gold.try_g.toLocaleString()} TL</p>`;
   document.getElementById('cryptoBox').innerHTML=d.crypto.map(c=>`<div style="display:flex;justify-content:space-between;padding:10px;border-bottom:1px solid #eee"><b>${c.n}</b><span>$${c.p.toLocaleString()} <small style="color:${c.c>=0?'#25D366':'#e53935'}">${c.c.toFixed(2)}%</small></span></div>`).join('');
 });
}
loadPrices();
setInterval(loadPrices,30000);
</script>
</body></html>'''

if __name__=='__main__':
    app.run(host='0.0.0.0',port=int(os.environ.get("PORT",10000)))
