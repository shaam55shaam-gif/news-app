from flask import Flask, request
import requests, feedparser, os, re, urllib.parse, concurrent.futures, time, json
app = Flask(__name__)
HEADERS={'User-Agent':'Mozilla/5.0'}
DATA_FILE="shami_data.json"

def load_data():
    try:
        with open(DATA_FILE,"r") as f: return json.load(f)
    except: return {"syp": 15250}
def save_data(d):
    try: open(DATA_FILE,"w").write(json.dumps(d))
    except: pass

SRC = {
 "عاجل 🔴": ["https://www.bbc.com/arabic/index.xml","https://www.aljazeera.net/xml/rss/all.xml","https://www.skynewsarabia.com/web/rss"],
 "رياضة ⚽": ["https://www.yallakora.com/rss/rss.aspx","https://www.bbc.com/arabic/sport/rss.xml","https://www.kooora.com/rss.aspx","https://www.france24.com/ar/tag/رياضة/rss"],
 "سياسة 🏛️": ["https://www.bbc.com/arabic/index.xml","https://www.france24.com/ar/rss","https://www.skynewsarabia.com/web/rss","https://arabic.cnn.com/rss"],
 "اقتصاد 💰": ["https://www.cnbcarabia.com/rss","https://www.alarabiya.net/.mrss/ar/business.xml","https://www.skynewsarabia.com/web/rss"],
 "فن 🎭": ["https://www.france24.com/ar/tag/ثقافة/rss","https://www.bbc.com/arabic/art-and-culture/rss.xml","https://www.skynewsarabia.com/web/rss"],
 "الكل": ["https://www.bbc.com/arabic/index.xml","https://www.france24.com/ar/rss","https://www.skynewsarabia.com/web/rss"]
}
CAT_COLORS = {"الكل":"#000","عاجل 🔴":"#ef4444","رياضة ⚽":"#22c55e","سياسة 🏛️":"#3b82f6","اقتصاد 💰":"#f59e0b","فن 🎭":"#a855f7"}

def get_img(entry):
    try:
        if hasattr(entry,'media_content') and entry.media_content:
            u=entry.media_content[0]['url']
            if u.startswith('http'): return u
        if hasattr(entry,'media_thumbnail') and entry.media_thumbnail:
            u=entry.media_thumbnail[0]['url']
            if u.startswith('http'): return u
        if hasattr(entry,'enclosures') and entry.enclosures:
            u=entry.enclosures[0].get('href','')
            if u.startswith('http'): return u
        html=""
        if hasattr(entry,'description'): html+=entry.description
        if hasattr(entry,'summary'): html+=entry.summary
        m=re.search(r'<img[^>]+src=["\']([^"\']+)["\']', html)
        if m:
            u=m.group(1)
            if u.startswith('//'): u='https:'+u
            if u.startswith('http'): return u
    except: pass
    return "https://images.unsplash.com/photo-1504711434969-e33886168f5c?w=600&h=400&fit=crop"

def fetch_one(url):
    try:
        r=requests.get(url,headers=HEADERS,timeout=7)
        f=feedparser.parse(r.content)
        out=[]
        for e in f.entries[:5]:
            out.append({"title":e.title,"link":e.link,"image":get_img(e),"source":url.split('/')[2].replace('www.','')})
        return out
    except: return []

def get_news(cat):
    urls=SRC.get(cat,SRC["الكل"])
    all_news=[]
    with concurrent.futures.ThreadPoolExecutor(max_workers=4) as ex:
        for res in ex.map(fetch_one, urls):
            all_news.extend(res)
    return all_news[:25]

def get_prices():
    d=load_data()
    # اسعار ثابتة + تحديث وقت
    return {"usd_syp":d.get("syp",15250),"gold":"$4,286","btc":"$84,123","time":time.strftime("%H:%M")}

@app.route('/')
def home():
    cat=request.args.get('cat','الكل')
    news=get_news(cat)
    ajel=get_news("عاجل 🔴")[:5]
    prices=get_prices()

    cats=["الكل","عاجل 🔴","رياضة ⚽","سياسة 🏛️","اقتصاد 💰","فن 🎭"]
    tabs_html=""
    for c in cats:
        active='active' if c==cat else ''
        col=CAT_COLORS.get(c,"#000")
        link="/?cat="+urllib.parse.quote(c)
        tabs_html+='<a href="'+link+'" class="'+active+'" style="border-color:'+col+'">'+c+'</a>'

    # شريط عاجل
    ajel_text=" | ".join([x["title"][:60] for x in ajel])
    ticker_html='<div class="ticker"><span class="live">عاجل 🔴</span><marquee>'+ajel_text+'</marquee></div>'

    # شريط عملات
    price_html='<div class="prices"><div>💵 دولار: '+str(prices["usd_syp"])+' ل.س</div><div>🥇 ذهب: '+prices["gold"]+'</div><div>₿ بيتكوين: '+prices["btc"]+'</div><div>'+prices["time"]+'</div></div>'

    cards_html=""
    for n in news:
        cards_html+='<div class="card"><img src="'+n["image"]+'" onerror="this.src=\'https://images.unsplash.com/photo-1504711434969-e33886168f5c?w=600\'"><div class="c"><span class="badge">'+cat+'</span><h3>'+n["title"]+'</h3><small>'+n["source"]+'</small><br><a class="link" href="'+n["link"]+'" target="_blank">اقرأ الخبر</a></div></div>'

    html="""<!DOCTYPE html><html dir="rtl" lang="ar"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1"><title>شامي نيوز</title>
<style>
body{font-family:system-ui,sans-serif;background:#f1f5f9;margin:0}
.header{background:#fff;padding:12px 15px;position:sticky;top:0;z-index:20;box-shadow:0 2px 10px #0001}
.header h2{margin:0 0 8px 0}
.prices{display:flex;gap:12px;overflow:auto;background:#111;color:#fff;padding:8px 12px;border-radius:10px;font-size:13px;white-space:nowrap}
.ticker{display:flex;align-items:center;background:#fef2f2;border:1px solid #fecaca;color:#b91c1c;padding:6px 10px;border-radius:10px;margin:10px;overflow:hidden}
.ticker.live{background:#ef4444;color:#fff;padding:4px 8px;border-radius:20px;font-weight:800;margin-left:10px;animation:blink 1s infinite}
@keyframes blink{0%{opacity:1}50%{opacity:0.5}100%{opacity:1}}
.tabs{display:flex;gap:8px;overflow:auto;padding:10px 12px}
.tabs a{padding:10px 18px;border-radius:25px;background:#fff;color:#333;text-decoration:none;font-weight:700;border:2px solid #e5e7eb;white-space:nowrap}
.tabs a.active{background:#000;color:#fff;border-color:#000}
.card{background:#fff;border-radius:18px;overflow:hidden;margin:12px;box-shadow:0 4px 15px #0001}
.card img{width:100%;height:200px;object-fit:cover;background:#e5e7eb}
.c{padding:12px}
.badge{display:inline-block;padding:3px 8px;border-radius:20px;background:#f3f4f6;font-size:11px;margin-bottom:6px}
.card h3{margin:4px 0 6px;font-size:17px;line-height:1.4}
.link{color:#7c3aed;text-decoration:none;font-weight:800}
</style></head><body>
<div class="header"><h2>شامي نيوز</h2>"""+price_html+"""</div>
"""+ticker_html+"""
<div class="tabs">"""+tabs_html+"""</div>
<div>"""+cards_html+"""</div>
</body></html>"""
    return html

@app.route('/health')
def health(): return "OK"

if __name__=='__main__':
    app.run(host='0.0.0.0',port=int(os.environ.get("PORT",10000)))
